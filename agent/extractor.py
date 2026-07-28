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

import re as _re_num

def _parse_first_page_number(raw) -> Optional[int]:
    """Parse robustement un numéro de page depuis n'importe quel format:
       '1', '1, 2, 3', '[1, 2, 3]', 'partie 1', 'Inconnue' → retourne 1 ou None."""
    if raw is None:
        return None
    s = str(raw)
    m = _re_num.search(r'\d+', s)
    if m:
        try:
            return int(m.group())
        except Exception:
            return None
    return None

# Helper to safely extract page numbers from document metadata
def get_page(doc):
    p = doc.metadata.get('page')
    if p is not None:
        n = _parse_first_page_number(p)
        if n is not None:
            return str(n)
        return str(p) if isinstance(p, str) else None
    pages = doc.metadata.get('pages')
    if pages is not None:
        if isinstance(pages, list) and len(pages) > 0:
            n = _parse_first_page_number(pages[0])
            return str(n) if n is not None else str(pages[0])
        if isinstance(pages, str) and pages.strip():
            n = _parse_first_page_number(pages)
            if n is not None:
                return str(n)
            return pages
    return None

async def _safe_ainvoke(llm, prompt_str: str, max_retries: int = 1):
    import re
    for attempt in range(max_retries + 1):
        try:
            return await llm.ainvoke(prompt_str)
        except Exception as e:
            err_str = str(e).lower()
            is_429 = "rate limit" in err_str or "429" in err_str
            if is_429 and attempt < (max_retries + 0):
                wait_time = 3.0
                m = re.search(r"try again in (\d+\.?\d*)s", err_str)
                if m:
                    wait_time = float(m.group(1)) + 0.2
                else:
                    m2 = re.search(r"limit (\d+), used (\d+), requested (\d+)", err_str)
                    if m2:
                        limit = int(m2.group(1))
                        used = int(m2.group(2))
                        req = int(m2.group(3))
                        over = max(0, used + req - limit)
                        if limit > 0 and over > 0:
                            ratio = (over / max(1, req))
                            wait_time = max(2.0, min(8.0, 60.0 * ratio))
                print(f"[Rate Limit] TPM atteint. Attente {wait_time:.1f}s (try {attempt+1}/{max_retries+1})")
                await asyncio.sleep(wait_time)
            else:
                if attempt >= max_retries:
                    raise e
                await asyncio.sleep(0.8)
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
                page_num = _parse_first_page_number(page_str)
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
                if doc_page and _parse_first_page_number(doc_page) == page_num:
                    best_extrait = doc.page_content[:200] + "..."
                    break
        else:
            if retrieved_docs:
                best_extrait = retrieved_docs[0].page_content[:200] + "..."
                doc_page = get_page(retrieved_docs[0])
                page_num = _parse_first_page_number(doc_page)
            
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
    ✅ QUALITÉ + VITESSE : Prompt CLAIR avec EXEMPLE, JSON strictement limité aux champs attendus.
    Nettoyage post-parsing : suppression des clés non attendues (garantie : plus de "list"/"dérivé"/"string")
    """
    import json
    import re as _re
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
    
    expected_keys = sorted(set(fi["champ"] for fi in fields_info))
    list_keys = sorted(set(fi["champ"] for fi in fields_info if fi["type"] == "list"))
    scalar_keys = sorted(set(fi["champ"] for fi in fields_info if fi["type"] != "list"))
    expected_keys_set = set(expected_keys)

    seen_keys = set()
    unique_docs = []

    async def _search_one(q_text: str, k: int):
        try:
            return await asyncio.to_thread(vectorstore.similarity_search, q_text, k=k)
        except Exception:
            return []

    if len(questions) <= 1:
        all_queries_text = ". ".join(q["question"] for q in questions)
        retrieved_docs = await _search_one(all_queries_text, 5)
    else:
        sub_tasks = [asyncio.create_task(_search_one(q["question"], k=3)) for q in questions]
        all_results = await asyncio.gather(*sub_tasks, return_exceptions=True)
        retrieved_docs = []
        for r in all_results:
            if isinstance(r, list):
                retrieved_docs.extend(r)

    for d in retrieved_docs:
        key = d.page_content[:120]
        if key not in seen_keys:
            seen_keys.add(key)
            unique_docs.append(d)

    unique_docs = unique_docs[:8]

    doc_infos = []
    context_parts = []
    total_chars = 0
    context_char_limit = 4500
    for i, doc in enumerate(unique_docs):
        doc_text = doc.page_content
        pg = None
        try:
            pg_raw = get_page(doc)
            pg = _parse_first_page_number(pg_raw)
        except Exception:
            pg = None
        doc_infos.append({"text": doc_text, "page": pg, "idx": i})
        if total_chars + len(doc_text) > context_char_limit:
            remaining = max(0, context_char_limit - total_chars)
            if remaining > 100:
                context_parts.append(f"[E{i+1}:{doc_text[:remaining]}]")
            break
        context_parts.append(f"[E{i+1}:{doc_text}]")
        total_chars += len(doc_text)
    context_text = " ".join(context_parts)

    questions_lines = "\n".join(
        f"- [{fi['champ']}] type={'LISTE' if fi['type']=='list' else 'TEXTE'} : {fi['question']}"
        for fi in fields_info
    )

    exemple_keys = expected_keys[:3] or expected_keys
    exemple_vals = {}
    for ek in exemple_keys:
        if ek in list_keys:
            exemple_vals[ek] = ["exemple A", "exemple B"]
        elif ek in scalar_keys:
            exemple_vals[ek] = "exemple valeur texte ou null"
    exemple_str = json.dumps(exemple_vals, ensure_ascii=False)

    list_reminder = (
        f"LISTE (valeur = [] ou [\"x\",\"y\"]): {', '.join(list_keys)}" if list_keys else "LISTE: (aucun)"
    )
    scalar_reminder = (
        f"TEXTE (valeur = \"...\" ou null): {', '.join(scalar_keys)}" if scalar_keys else "TEXTE: (aucun)"
    )

    prompt_str = (
        "Tu extrais des informations d'un document. REPONSE UNIQUE = OBJECT JSON VALIDE.\n"
        f"CLÉS JSON AUTORISÉES (OBLIGATOIRE d'utiliser UNIQUEMENT ces noms): {', '.join(expected_keys)}\n"
        f"{scalar_reminder}\n"
        f"{list_reminder}\n"
        "\n"
        "RÈGLES:\n"
        "- Info ABSENTE du document → valeur = null (pour TEXTE) ou [] (pour LISTE)\n"
        "- Ne JAMAIS inventer, ne JAMAIS déduire si ce n'est pas écrit\n"
        "- Ne PAS ajouter de clés. Ne PAS utiliser \"total\", \"list\", \"dérivé\", \"string\", \"début\", \"durée\" comme clés\n"
        "\n"
        "QUESTIONS:\n"
        f"{questions_lines}\n"
        "\n"
        f"EXEMPLE FORMAT ATTENDU: {exemple_str}\n"
        "\n"
        "DOCUMENT (extraits):\n"
        f"{context_text}\n"
        "\n"
        "JSON FINAL:"
    )

    def _find_source_for_value(raw_v):
        if raw_v is None or (isinstance(raw_v, str) and not raw_v.strip()):
            return None, None
        v_texts = []
        if isinstance(raw_v, list):
            for x in raw_v:
                if x is not None:
                    v_texts.append(str(x))
        else:
            v_texts.append(str(raw_v))
        best_page = None
        best_extrait = None
        best_score = 0
        for di in doc_infos:
            dt_lower = di["text"].lower()
            score = 0
            matched_any = False
            for vt in v_texts:
                vlow = vt.lower().strip()
                if not vlow:
                    continue
                if len(vlow) >= 4 and vlow in dt_lower:
                    score += len(vlow)
                    matched_any = True
                else:
                    for word in vlow.split():
                        w = word.strip(" ,.;:!?()[]\"'-")
                        if len(w) >= 4 and w in dt_lower:
                            score += 2
                            matched_any = True
            if matched_any and score > best_score:
                best_score = score
                best_page = di["page"]
                trunc = di["text"][:200]
                best_extrait = trunc + ("..." if len(di["text"]) > 200 else "")
        return best_page, best_extrait

    try:
        if semaphore:
            async with semaphore:
                response = await _safe_ainvoke(llm, prompt_str, max_retries=1)
        else:
            response = await _safe_ainvoke(llm, prompt_str, max_retries=1)

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

        parsed = None
        try:
            parsed = json.loads(json_str)
        except Exception:
            start = json_str.find("{")
            end = json_str.rfind("}")
            if start != -1 and end != -1 and end > start:
                try:
                    parsed = json.loads(json_str[start:end+1])
                except Exception:
                    try:
                        fixed = json_str.replace("\n", " ").replace("\r", " ").replace("\t", " ")
                        fixed = _re.sub(r',\s*}', '}', fixed)
                        fixed = _re.sub(r',\s*]', ']', fixed)
                        parsed = json.loads(fixed)
                    except Exception:
                        try:
                            parsed = _heuristic_extract_values_from_text(raw_text, fields_info)
                        except Exception:
                            pass

        if parsed is None:
            parsed = {}
        if not isinstance(parsed, dict):
            parsed = {}

        # FILTRAGE CRUCIAL: ne garder QUE les clés attendues
        # Supprime "total"/"list"/"dérivé"/"string"/"début"/"durée" et toute clé parasite
        cleaned = {}
        for k, v in parsed.items():
            if k in expected_keys_set:
                cleaned[k] = v

        parsed = cleaned

        for fi in fields_info:
            champ = fi["champ"]
            is_list = fi["type"] == "list"
            if champ not in parsed:
                if is_list:
                    category_results[champ] = {"valeur": [], "source": None, "confiance": 0.0}
                else:
                    category_results[champ] = {"valeur": None, "source": None, "confiance": 0.0}
                continue

            raw_v = parsed[champ]
            if isinstance(raw_v, str) and raw_v.strip() == "":
                raw_v = None
            if isinstance(raw_v, str) and ("NON_TROUVE" in raw_v.upper() or raw_v.lower().strip() == "null"):
                raw_v = None

            page_num, extrait = _find_source_for_value(raw_v)
            source_obj = None
            if page_num is not None or extrait:
                source_obj = {"page": page_num, "section": None, "extrait": extrait}

            if is_list:
                if isinstance(raw_v, list):
                    clean = [str(v).strip() for v in raw_v if v is not None and str(v).strip()]
                    category_results[champ] = {"valeur": clean, "source": source_obj, "confiance": 0.85 if clean else 0.0}
                else:
                    if raw_v is None:
                        category_results[champ] = {"valeur": [], "source": None, "confiance": 0.0}
                    else:
                        single = str(raw_v).strip()
                        category_results[champ] = {
                            "valeur": [s for s in [x.strip() for x in single.split(",")] if s],
                            "source": source_obj,
                            "confiance": 0.85
                        }
            else:
                if raw_v is None:
                    category_results[champ] = {"valeur": None, "source": None, "confiance": 0.0}
                elif isinstance(raw_v, list):
                    vs = " ".join(str(x) for x in raw_v if x is not None)
                    if not vs.strip():
                        category_results[champ] = {"valeur": None, "source": None, "confiance": 0.0}
                    else:
                        category_results[champ] = {"valeur": vs, "source": source_obj, "confiance": 0.85}
                elif isinstance(raw_v, bool) or isinstance(raw_v, (int, float)):
                    category_results[champ] = {"valeur": str(raw_v), "source": source_obj, "confiance": 0.85}
                else:
                    category_results[champ] = {"valeur": str(raw_v), "source": source_obj, "confiance": 0.85}

        for fi in fields_info:
            if fi["champ"] not in category_results:
                if fi["type"] == "list":
                    category_results[fi["champ"]] = {"valeur": [], "source": None, "confiance": 0.0}
                else:
                    category_results[fi["champ"]] = {"valeur": None, "source": None, "confiance": 0.0}

        return category_results

    except Exception as e:
        print(f"[BATCH] {category_name}: batch failed ({e}). RETOUR NULL rapide")
        for fi in fields_info:
            if fi["type"] == "list":
                category_results[fi["champ"]] = {"valeur": [], "source": None, "confiance": 0.0}
            else:
                category_results[fi["champ"]] = {"valeur": None, "source": None, "confiance": 0.0}
        return category_results


def _heuristic_extract_values_from_text(text: str, fields_info):
    """
    Dernier recours : extraire des valeurs potentielles par regex/keyword scanning
    lorsque le LLM a renvoyé un texte non JSON.
    """
    import re
    result = {}
    for fi in fields_info:
        champ = fi["champ"]
        q = fi["question"]
        keywords = set()
        for w in re.split(r"\W+", q.lower()):
            if len(w) >= 5:
                keywords.add(w)
        for line in text.split("\n"):
            if champ in line:
                m = re.search(rf"{re.escape(champ)}\s*[:=]\s*(.+)", line, re.IGNORECASE)
                if m:
                    raw = m.group(1).strip().strip("\"'`").rstrip(",").rstrip(";").strip()
                    if raw.upper().startswith("NON_TROUVE") or raw in ("null", "NULL"):
                        result[champ] = None
                    else:
                        result[champ] = raw
                    break
    return result


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
    
    # Groq TPM = 6000 → limiter la concurrence à 2-3 SINON on explose la limite
    # Si TPM atteint, on attend 10+ secondes, ce qui est PIRE que d'aller lentement mais sûrement
    default_limit = 2
    try:
        env_limit = int(os.getenv("AGENT_CONCURRENCY_LIMIT", "").strip() or default_limit)
    except Exception:
        env_limit = default_limit
    concurrency_limit = max(1, min(3, env_limit))
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
    
    async def _run_cat(cat_key: str, schema_key: str, stagger_s: float):
        if stagger_s > 0:
            await asyncio.sleep(stagger_s)
        t_cat0 = time.perf_counter()
        _dbg("agent.category.start", category=cat_key, questions=len(dynamic_queries.get(cat_key) or []), stagger=stagger_s)
        cat_data = await _extract_category_data_batched(
            category_name=cat_key,
            questions=dynamic_queries[cat_key],
            vectorstore=vectorstore,
            llm=llm,
            semaphore=semaphore
        )
        _dbg("agent.category.done", category=cat_key, ms=(time.perf_counter() - t_cat0) * 1000.0)
        return schema_key, cat_data

    tasks = []
    for i, (cat_key, schema_key) in enumerate(zip(active_cats_keys, category_keys)):
        stagger = 0.0 if concurrency_limit > len(active_cats_keys) else round(0.25 * i, 3)
        tasks.append(asyncio.create_task(_run_cat(cat_key, schema_key, stagger)))
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
