import asyncio
import os
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
from agent.vectorstore import get_chroma_vectorstore, load_config
from agent.analyzer import analyze_document_type
from agent.prompts import build_dynamic_queries, get_empty_category_result
from schema.v1.models import CopilotExtraction, MetaInfo

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

async def _safe_ainvoke(llm, prompt_str: str, max_retries: int = 5):
    import re
    for attempt in range(max_retries):
        try:
            return await llm.ainvoke(prompt_str)
        except Exception as e:
            err_str = str(e).lower()
            if "rate limit" in err_str or "429" in err_str:
                wait_time = 10.0
                m = re.search(r"try again in (\d+\.?\d*)s", err_str)
                if m:
                    wait_time = float(m.group(1)) + 1.0
                print(f"[Rate Limit] Limite API atteinte. Attente de {wait_time:.2f}s (Tentative {attempt+1}/{max_retries})...")
                await asyncio.sleep(wait_time)
            else:
                raise e
    return await llm.ainvoke(prompt_str)

async def _process_single_field(q_info: Dict[str, str], vectorstore, llm, top_k: int = 3, semaphore: asyncio.Semaphore = None):
    champ = q_info["champ"]
    question = q_info["question"]
    is_list = q_info["type"] == "list"
    
    # 1. Retrieval (Recherche vectorielle)
    retrieved_docs = vectorstore.similarity_search(question, k=top_k)
        
    context_text = "\n\n".join(
        [f"--- Extrait {i+1} (Page {get_page(doc)}) ---\n{doc.page_content}" 
         for i, doc in enumerate(retrieved_docs)]
    )
    
    # 2. Prompting strict
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
        
        # 3. Parsing de la réponse
        if response == "NON_TROUVE" or response == "" or "NON_TROUVE" in response:
            if is_list:
                return champ, {"valeur": [], "source": None, "confiance": 0.0}
            else:
                return champ, {"valeur": None, "source": None, "confiance": 0.0}
            
        # Extraction basique de la page
        page_num = None
        if "[Page " in response:
            try:
                page_str = response.split("[Page ")[1].split("]")[0]
                if page_str.isdigit():
                    page_num = int(page_str)
                elif page_str.lower() != "inconnue":
                    # Essayer d'extraire juste les chiffres si possible (ex: "1, 2" -> 1)
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
            
        # Trouver l'extrait le plus pertinent pour la justification (celui de la bonne page si possible)
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
                # Essayer de récupérer la page du premier document si on n'en a pas
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
            "confiance": 0.85 # Confiance arbitraire pour l'instant
        }
        
    except Exception as e:
        print(f"Erreur d'extraction pour le champ {champ}: {e}")
        if is_list:
            return champ, {"valeur": [], "source": None, "confiance": 0.0}
        else:
            return champ, {"valeur": None, "source": None, "confiance": 0.0}
            
async def _extract_category_data(
    category_name: str,
    questions: List[Dict[str, str]],
    vectorstore,
    llm,
    top_k: int = 3,
    semaphore: asyncio.Semaphore = None
) -> Dict[str, Any]:
    """
    Extrait les données pour une catégorie spécifique en utilisant le RAG (en PARALLÈLE).
    """
    category_results = {}
    
    # ✅ PARALLÉLISATION : Traiter tous les champs de la catégorie en même temps
    tasks = [_process_single_field(q_info, vectorstore, llm, top_k, semaphore) for q_info in questions]
    field_results = await asyncio.gather(*tasks)
    
    for champ, value in field_results:
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
    print(f"\n[Agent] Début de l'extraction pour {file_path}")
    
    # ÉTAPE 1 : Analyse préliminaire du document
    print("[Agent] Étape 1: Analyse préliminaire (Routing)...")
    categories_detectees = analyze_document_type(file_path, provider, model, config_path)
    active_cats = categories_detectees.get_active_categories()
    print(f"[Agent] Catégories détectées : {active_cats}")
    
    # ÉTAPE 2 : Génération des questions dynamiques
    print("[Agent] Étape 2: Génération des requêtes dynamiques...")
    dynamic_queries = build_dynamic_queries(categories_detectees)
    
    # Préparation des outils RAG
    llm = get_llm(provider=provider, model=model, config_path=config_path, temperature=0.0)
    config = load_config(config_path)
    vectorstore = get_chroma_vectorstore(config)
    
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
    
    # ÉTAPE 3 : Extraction RAG ciblée (PARALLÉLISATION DES CATÉGORIES)
    print("[Agent] Étape 3: Extraction RAG ciblée...")
    
    # Création d'un sémaphore pour limiter le nombre de requêtes LLM simultanées
    # et éviter de saturer le Rate Limit de l'API (ex: Groq 6000 TPM)
    concurrency_limit = 3
    semaphore = asyncio.Semaphore(concurrency_limit)
    
    # Collecter toutes les tâches async pour les catégories actives
    category_tasks = []
    category_keys = []
    
    for cat_key, schema_key in schema_mapping.items():
        if cat_key in active_cats and cat_key in dynamic_queries:
            print(f"  -> Extraction de la catégorie : {cat_key} ({len(dynamic_queries[cat_key])} questions)")
            # Ajouter la tâche async pour cette catégorie
            category_tasks.append(
                _extract_category_data(
                    category_name=cat_key,
                    questions=dynamic_queries[cat_key],
                    vectorstore=vectorstore,
                    llm=llm,
                    semaphore=semaphore
                )
            )
            category_keys.append(schema_key)
        else:
            print(f"  -> Catégorie ignorée : {cat_key} (génération de valeurs nulles)")
            raw_results[schema_key] = get_empty_category_result(cat_key)
    
    # ✅ Exécuter toutes les catégories en parallèle avec asyncio.gather
    category_results_list = await asyncio.gather(*category_tasks)
    
    # Ajouter les résultats de chaque catégorie
    for schema_key, cat_data in zip(category_keys, category_results_list):
        raw_results[schema_key] = cat_data
            
    # ÉTAPE 4 : Validation Pydantic
    print("[Agent] Étape 4: Validation Pydantic...")
    try:
        validated_data = CopilotExtraction(**raw_results)
        # Utiliser model_dump(mode='json') pour s'assurer que les dates sont des strings
        return validated_data.model_dump(mode='json')
    except ValidationError as e:
        print(f"[Agent] ERREUR DE VALIDATION PYDANTIC: {e}")
        # En cas d'erreur de validation (ça ne devrait pas arriver avec notre gestion des fallback),
        # on renvoie le brut pour déboguer.
        return raw_results
