import asyncio
import os
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

from langchain_core.prompts import PromptTemplate
from pydantic import ValidationError

from agent.llm_provider import LLMProvider

def get_llm(provider: Optional[str] = None, model: Optional[str] = None, config_path: str = "config.yaml", temperature: float = 0.0):
    llm_manager = LLMProvider(provider=provider, model=model, config_path=config_path)
    if temperature != 0.0:
        llm_manager.llm.temperature = temperature
    return llm_manager.llm
from agent.vectorstore import get_chroma_vectorstore, load_config, get_embeddings
from agent.analyzer import analyze_document_type
from agent.prompts import build_dynamic_queries, get_empty_category_result
from schema.v1.models import CopilotExtraction, MetaInfo

#region debug-point extract-slow-performance
import requests

def _dbg(event: str, **data: Any) -> None:
    url = os.getenv("DEBUG_SERVER_URL")
    if not url:
        return
    payload = {
        "sessionId": os.getenv("DEBUG_SESSION_ID"),
        "event": event,
        "ts": time.time(),
        **data,
    }
    try:
        requests.post(url, json=payload, timeout=0.8)
    except Exception:
        return
#endregion debug-point extract-slow-performance

# Helper to safely extract page numbers from document metadata
def get_page(doc):
    p = doc.metadata.get('page')
    if p is not None:
        return str(p)
    pages = doc.metadata.get('pages')
    if pages and len(pages) > 0:
        if isinstance(pages, list):
            return str(pages[0])
        return str(pages)
    return 'Inconnue'

async def _safe_ainvoke(llm, prompt_str: str, max_retries: int = 2):
    import re
    for attempt in range(max_retries):
        try:
            return await llm.ainvoke(prompt_str)
        except Exception as e:
            err_str = str(e).lower()
            if "rate limit" in err_str or "429" in err_str:
                wait_time = 3.0
                m = re.search(r"try again in (\d+\.?\d*)s", err_str)
                if m:
                    wait_time = float(m.group(1)) + 0.5
                print(f"[Rate Limit] Limite API atteinte. Attente de {wait_time:.2f}s (Tentative {attempt+1}/{max_retries})...")
                await asyncio.sleep(wait_time)
            else:
                if attempt == max_retries - 1:
                    raise e
                await asyncio.sleep(1.0)
    return await llm.ainvoke(prompt_str)

async def _process_single_field(q_info: Dict[str, str], vectorstore, llm, top_k: int = 2, semaphore: asyncio.Semaphore = None):
    champ = q_info["champ"]
    question = q_info["question"]
    is_list = q_info["type"] == "list"
    
    retrieved_docs = await asyncio.to_thread(vectorstore.similarity_search, question, k=top_k)
        
    context_text = "\n\n".join(
        [f"--- Extrait {i+1} (Page {get_page(doc)}) ---\n{doc.page_content}" 
         for i, doc in enumerate(retrieved_docs)]
    )
    
    if len(context_text) > 2500:
        context_text = context_text[:2500] + "\n...[Tronqué]"
    
    prompt_str = f"""Tu es un expert en analyse de documents d'entreprise.
Ta mission est de répondre à la question suivante en te basant UNIQUEMENT sur le contexte fourni.
Si l'information n'est pas présente dans le contexte, tu DOIS répondre "NON_TROUVE". Ne devine rien.

Question : {question}

Contexte :
{context_text}

Règles de formatage de ta réponse :
1. Donne uniquement la valeur demandée, sans phrase d'introduction.
2. Si tu as trouvé l'information, indique le numéro de la page source entre crochets à la fin de ta réponse (ex: [Page 12]).
3. Si la question attend une liste (ex: concurrents), sépare les éléments par des virgules.
"""
    
    try:
        if semaphore:
            async with semaphore:
                response = await _safe_ainvoke(llm, prompt_str)
        else:
            response = await _safe_ainvoke(llm, prompt_str)
            
        response = response.content.strip()
        
        if response == "NON_TROUVE" or response == "" or "NON_TROUVE" in response:
            if is_list:
                return champ, {"valeur": [], "source": None, "confiance": 0.0}
            else:
                return champ, {"valeur": None, "source": None, "confiance": 0.0}
            
        page_num = None
        if "[Page " in response:
            try:
                page_str = response.split("[Page ")[1].split("]")[0]
                if page_str.isdigit():
                    page_num = int(page_str)
                elif page_str.lower() != "inconnue":
                    import re
                    m = re.search(r'\d+', page_str)
                    if m:
                        page_num = int(m.group())
                response = response.split("[Page ")[0].strip()
            except:
                pass
                
        if is_list:
            valeur = [v.strip() for v in response.split(",") if v.strip()]
        else:
            valeur = response
            
        best_extrait = context_text[:200] + "..."
        if page_num is not None:
            for doc in retrieved_docs:
                doc_page = get_page(doc)
                if str(page_num) == doc_page:
                    best_extrait = doc.page_content[:200] + "..."
                    break
        else:
            if retrieved_docs:
                best_extrait = retrieved_docs[0].page_content[:200] + "..."
                doc_page = get_page(retrieved_docs[0])
                if doc_page and doc_page.isdigit():
                    page_num = int(doc_page)
            
        return champ, {
            "valeur": valeur,
            "source": {
                "page": page_num,
                "section": None,
                "extrait": best_extrait
            },
            "confiance": 0.85
        }
        
    except Exception as e:
        print(f"Erreur d'extraction pour le champ {champ}: {e}")
        if is_list:
            return champ, {"valeur": [], "source": None, "confiance": 0.0}
        else:
            return champ, {"valeur": None, "source": None, "confiance": 0.0}


async def _extract_category_data_batched(
    category_name: str,
    questions: List[Dict[str, str]],
    vectorstore,
    llm,
    semaphore: asyncio.Semaphore = None
) -> Dict[str, Any]:
    """
    ✅ VERSION OPTIMISÉE : 1 SEUL APPEL LLM PAR CATÉGORIE (au lieu de 1 par champ)
    Toutes les questions d'une catégorie sont envoyées EN MÊME TEMPS au LLM,
    qui répond avec un JSON structuré contenant TOUTES les valeurs.
    Divise par ~4 à ~7 le temps d'exécution de cette étape.
    """
    import json
    category_results = {}
    
    if not questions:
        return category_results

    fields_info = []
    for q_info in questions:
        fields_info.append({
            "champ": q_info["champ"],
            "question": q_info["question"],
            "type": q_info["type"]
        })
    
    all_queries_text = " ".join(q["question"] for q in questions)
    retrieved_docs = await asyncio.to_thread(vectorstore.similarity_search, all_queries_text, k=3)
    
    all_per_field_docs = []
    retrieval_task = [
        asyncio.create_task(asyncio.to_thread(vectorstore.similarity_search, q_info["question"], k=1))
        for q_info in questions
    ]
    per_field_results = await asyncio.gather(*retrieval_task, return_exceptions=True)
    for r in per_field_results:
        if isinstance(r, list):
            all_per_field_docs.extend(r)

    combined_docs = retrieved_docs + all_per_field_docs
    seen_contents = set()
    unique_docs = []
    for d in combined_docs:
        content = d.page_content[:100]
        if content not in seen_contents:
            seen_contents.add(content)
            unique_docs.append(d)
    
    context_parts = []
    total_chars = 0
    for i, doc in enumerate(unique_docs[:8]):
        doc_text = doc.page_content
        if total_chars + len(doc_text) > 3500:
            remaining = max(0, 3500 - total_chars)
            if remaining > 100:
                context_parts.append(f"--- Extrait {i+1} (Page {get_page(doc)}) ---\n{doc_text[:remaining]}\n...[Tronqué]")
            break
        context_parts.append(f"--- Extrait {i+1} (Page {get_page(doc)}) ---\n{doc_text}")
        total_chars += len(doc_text)
    context_text = "\n\n".join(context_parts)

    fields_json_schema = {}
    for fi in fields_info:
        if fi["type"] == "list":
            fields_json_schema[fi["champ"]] = {
                "type": "object",
                "properties": {
                    "valeur": {"type": "array", "items": {"type": "string"}, "description": "Liste des valeurs trouvées, tableau vide si non trouvé"},
                    "page": {"type": ["integer", "null"], "description": "Numéro de page source, null si non trouvé"},
                    "extrait": {"type": ["string", "null"], "description": "Extrait source court, null si non trouvé"}
                },
                "required": ["valeur", "page", "extrait"]
            }
        else:
            fields_json_schema[fi["champ"]] = {
                "type": "object",
                "properties": {
                    "valeur": {"type": ["string", "null"], "description": "Valeur trouvée, null si NON_TROUVE"},
                    "page": {"type": ["integer", "null"], "description": "Numéro de page source, null si non trouvé"},
                    "extrait": {"type": ["string", "null"], "description": "Extrait source court (≤ 200 chars), null si non trouvé"}
                },
                "required": ["valeur", "page", "extrait"]
            }

    questions_list_str = "\n".join(
        f"- [{fi['champ']}] (type: {fi['type']}) {fi['question']}"
        for fi in fields_info
    )

    prompt_str = f"""Tu es un expert en extraction d'informations de documents d'entreprise.

OBJECTIF : Répondre à TOUTES les questions suivantes EN MÊME TEMPS à partir du contexte fourni.
RÈGLE ABSOLUE : Si une information n'est PAS explicitement dans le contexte, tu DOIS mettre valeur = null ET page = null ET extrait = null. NE DEVINE JAMAIS RIEN.

LISTE DES QUESTIONS :
{questions_list_str}

CONTEXTE (extraits du document) :
{context_text}

FORMAT DE RÉPONSE OBLIGATOIRE :
Tu DOIS répondre UNIQUEMENT avec un objet JSON valide, sans phrase d'introduction ni conclusion.
Le JSON doit avoir pour clé le NOM DU CHAMP (ex: "chiffre_affaires"), et pour valeur un objet :
{{
  "nom_du_champ_1": {{
    "valeur": "la valeur trouvée OU null si absente",
    "page": 12 OU null,
    "extrait": "extrait du contexte qui prouve la réponse (max 200 caractères) OU null"
  }},
  "nom_du_champ_2": {{
    "valeur": ["item1", "item2"] OU [] si liste vide / non trouvé,
    "page": 5 OU null,
    "extrait": "..." OU null
  }}
}}

Autres règles :
- Pour un champ de type "field" : "valeur" est une string ou null
- Pour un champ de type "list"  : "valeur" est un tableau (array) de strings, ou [] si rien n'est trouvé
- Le numéro de page DOIT être un entier, ou null si on ne sait pas
- L'extrait DOIT être une portion exacte du contexte qui contient l'information
- RÉPONSE UNIQUE : JSON VALIDE, RIEN D'AUTRE. Ne pas encadrer de ```json...```."""

    try:
        if semaphore:
            async with semaphore:
                response = await _safe_ainvoke(llm, prompt_str, max_retries=2)
        else:
            response = await _safe_ainvoke(llm, prompt_str, max_retries=2)

        raw_text = response.content.strip()
        json_str = raw_text
        if "```json" in raw_text:
            json_str = raw_text.split("```json", 1)[1]
            if "```" in json_str:
                json_str = json_str.rsplit("```", 1)[0]
        elif "```" in raw_text:
            json_str = raw_text.split("```", 1)[1]
            if "```" in json_str:
                json_str = json_str.rsplit("```", 1)[0]
        json_str = json_str.strip()

        try:
            parsed = json.loads(json_str)
        except Exception:
            start = json_str.find("{")
            end = json_str.rfind("}")
            if start != -1 and end != -1 and end > start:
                json_str = json_str[start:end+1]
                parsed = json.loads(json_str)
            else:
                raise ValueError(f"Impossible de parser la réponse JSON du LLM pour la catégorie {category_name}")

        for fi in fields_info:
            champ = fi["champ"]
            is_list = fi["type"] == "list"
            entry = parsed.get(champ)

            if not isinstance(entry, dict):
                if is_list:
                    category_results[champ] = {"valeur": [], "source": None, "confiance": 0.0}
                else:
                    category_results[champ] = {"valeur": None, "source": None, "confiance": 0.0}
                continue

            raw_valeur = entry.get("valeur")
            raw_page = entry.get("page")
            raw_extrait = entry.get("extrait")

            page_num = None
            if isinstance(raw_page, int):
                page_num = raw_page
            elif isinstance(raw_page, str) and raw_page.isdigit():
                page_num = int(raw_page)

            source_obj = None
            if page_num is not None or (isinstance(raw_extrait, str) and raw_extrait.strip()):
                source_obj = {
                    "page": page_num,
                    "section": None,
                    "extrait": (str(raw_extrait)[:200] + "...") if isinstance(raw_extrait, str) and len(raw_extrait) > 200 else raw_extrait if raw_extrait else None
                }

            if is_list:
                if isinstance(raw_valeur, list):
                    clean_list = [str(v).strip() for v in raw_valeur if v is not None and str(v).strip()]
                    category_results[champ] = {"valeur": clean_list, "source": source_obj, "confiance": 0.85 if clean_list else 0.0}
                else:
                    category_results[champ] = {"valeur": [], "source": source_obj if raw_valeur else None, "confiance": 0.0}
            else:
                if raw_valeur is None or (isinstance(raw_valeur, str) and (raw_valeur.strip() == "" or "NON_TROUVE" in raw_valeur.upper())):
                    category_results[champ] = {"valeur": None, "source": None, "confiance": 0.0}
                else:
                    category_results[champ] = {"valeur": str(raw_valeur), "source": source_obj, "confiance": 0.85}

        for fi in fields_info:
            if fi["champ"] not in category_results:
                if fi["type"] == "list":
                    category_results[fi["champ"]] = {"valeur": [], "source": None, "confiance": 0.0}
                else:
                    category_results[fi["champ"]] = {"valeur": None, "source": None, "confiance": 0.0}

        return category_results

    except Exception as e:
        print(f"[BATCH] Catégorie {category_name} : échec du mode batch ({e}), fallback vers mode séquentiel.")
        tasks = [
            asyncio.create_task(_process_single_field(q_info, vectorstore, llm, 1, semaphore))
            for q_info in questions
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for res in results:
            if isinstance(res, Exception):
                continue
            champ, value = res
            category_results[champ] = value
        return category_results


async def _extract_category_data(
    category_name: str,
    questions: List[Dict[str, str]],
    vectorstore,
    llm,
    top_k: int = 2,
    semaphore: asyncio.Semaphore = None
) -> Dict[str, Any]:
    """
    Extrait les données pour une catégorie spécifique en utilisant le RAG (en PARALLÈLE).
    """
    category_results = {}
    
    tasks = [
        asyncio.create_task(_process_single_field(q_info, vectorstore, llm, top_k, semaphore))
        for q_info in (questions or [])
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    for res in results:
        if isinstance(res, Exception):
            continue
        champ, value = res
        category_results[champ] = value
                
    return category_results


async def run_agent_extraction(
    file_path: str,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    config_path: str = "config.yaml"
) -> Dict[str, Any]:
    """
    Pipeline principal de l'Agent RAG (Phase 4).
    1. Analyse préliminaire (T4.0)
    2. Génération de questions dynamiques
    3. RAG ciblé (PARALLÉLE)
    4. Validation Pydantic (Phase 5)
    """
    t0 = time.perf_counter()
    _dbg("agent.start", file_path=file_path, provider=provider, model=model)
    print(f"\n[Agent] Début de l'extraction pour {file_path}")
    
    # ÉTAPE 1 : Analyse préliminaire du document
    print("[Agent] Étape 1: Analyse préliminaire (Routing)...")
    t_route0 = time.perf_counter()
    categories_detectees = analyze_document_type(file_path, provider, model, config_path)
    active_cats = categories_detectees.get_active_categories()
    _dbg("agent.routing.done", file_path=file_path, ms=(time.perf_counter() - t_route0) * 1000.0, active_cats=active_cats)
    print(f"[Agent] Catégories détectées : {active_cats}")
    
    # ÉTAPE 2 : Génération des questions dynamiques
    print("[Agent] Étape 2: Génération des requêtes dynamiques...")
    t_q0 = time.perf_counter()
    dynamic_queries = build_dynamic_queries(categories_detectees)
    _dbg("agent.dynamic_queries.done", file_path=file_path, ms=(time.perf_counter() - t_q0) * 1000.0)
    
    # Préparation des outils RAG
    t_llm0 = time.perf_counter()
    llm = get_llm(provider=provider, model=model, config_path=config_path, temperature=0.0)
    _dbg("agent.llm.done", ms=(time.perf_counter() - t_llm0) * 1000.0)
    config = load_config(config_path)
    t_emb0 = time.perf_counter()
    embeddings = get_embeddings(config)
    _dbg("agent.embeddings.done", ms=(time.perf_counter() - t_emb0) * 1000.0)
    
    # Charger le vectorstore FAISS créé par _index_single_file
    from agent.vectorstore import get_or_create_faiss_vectorstore
    doc_name = os.path.basename(file_path).split('.')[0]
    t_vs0 = time.perf_counter()
    vectorstore = await asyncio.to_thread(
        get_or_create_faiss_vectorstore,
        [],
        doc_name,
        embeddings,
        config,
    )
    _dbg("agent.vectorstore.done", doc_name=doc_name, ms=(time.perf_counter() - t_vs0) * 1000.0)
    
    # Dictionnaire brut qui contiendra toutes les réponses
    raw_results = {}
    
    # Méta-informations
    base_name = os.path.basename(file_path)
    entreprise_name = os.path.splitext(base_name)[0]
    
    # Construire la liste des questions utilisées
    questions_list = []
    for cat_q in dynamic_queries.values():
        questions_list.extend(cat_q)
    
    raw_results["meta"] = {
        "entreprise": entreprise_name,
        "annee_rapport": None,
        "date_extraction": datetime.now().isoformat(),
        "modele_utilise": model or "default",
        "provider": provider or "default",
        "approche": "Agent_Final_T4",
        "source_file": file_path,
        "questions_utilisees": questions_list
    }
    
    # Mapping entre nos catégories internes et les noms du schéma JSON
    schema_mapping = {
        "strategique": "diagnostic_strategique",
        "financier": "diagnostic_financier",
        "rh": "diagnostic_rh",
        "data": "diagnostic_data",
        "cyber": "diagnostic_cyber_gouvernance"
    }
    
    # ÉTAPE 3 : Extraction RAG ciblée (PARALLÉLISATION DES CATÉGORIES + BATCH PAR CATÉGORIE)
    print("[Agent] Étape 3: Extraction RAG ciblée...")
    
    # Augmentation de la concurrence : Groq supporte bien 5 requêtes en parallèle
    default_limit = 5 if (provider or "").lower() in {"groq", "openai"} else 3
    try:
        env_limit = int(os.getenv("AGENT_CONCURRENCY_LIMIT", "").strip() or default_limit)
    except Exception:
        env_limit = default_limit
    concurrency_limit = max(3, min(10, env_limit))
    semaphore = asyncio.Semaphore(concurrency_limit)
    
    active_cats_keys = []
    category_keys = []
    
    for cat_key, schema_key in schema_mapping.items():
        if cat_key in active_cats and cat_key in dynamic_queries:
            print(f"  -> Extraction de la catégorie : {cat_key} ({len(dynamic_queries[cat_key])} questions en MODE BATCH 1 appel LLM)")
            active_cats_keys.append(cat_key)
            category_keys.append(schema_key)
        else:
            print(f"  -> Catégorie ignorée : {cat_key} (génération de valeurs nulles)")
            raw_results[schema_key] = get_empty_category_result(cat_key)
    
    async def _run_cat(cat_key: str, schema_key: str):
        t_cat0 = time.perf_counter()
        _dbg("agent.category.start", category=cat_key, questions=len(dynamic_queries.get(cat_key) or []))
        cat_data = await _extract_category_data_batched(
            category_name=cat_key,
            questions=dynamic_queries[cat_key],
            vectorstore=vectorstore,
            llm=llm,
            semaphore=semaphore
        )
        _dbg("agent.category.done", category=cat_key, ms=(time.perf_counter() - t_cat0) * 1000.0)
        return schema_key, cat_data

    tasks = [
        asyncio.create_task(_run_cat(cat_key, schema_key))
        for cat_key, schema_key in zip(active_cats_keys, category_keys)
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    for res in results:
        if isinstance(res, Exception):
            continue
        schema_key, cat_data = res
        raw_results[schema_key] = cat_data
            
    # ÉTAPE 4 : Validation Pydantic
    print("[Agent] Étape 4: Validation Pydantic...")
    try:
        t_val0 = time.perf_counter()
        validated_data = CopilotExtraction(**raw_results)
        _dbg("agent.validation.done", ms=(time.perf_counter() - t_val0) * 1000.0)
        # Utiliser model_dump(mode='json') pour s'assurer que les dates sont des strings
        _dbg("agent.done", file_path=file_path, ms=(time.perf_counter() - t0) * 1000.0)
        return validated_data.model_dump(mode='json')
    except ValidationError as e:
        print(f"[Agent] ERREUR DE VALIDATION PYDANTIC: {e}")
        _dbg("agent.validation.error", error=str(e))
        # En cas d'erreur de validation (ça ne devrait pas arriver avec notre gestion des fallback),
        # on renvoie le brut pour déboguer.
        _dbg("agent.done", file_path=file_path, ms=(time.perf_counter() - t0) * 1000.0)
        return raw_results
