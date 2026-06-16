import asyncio
import os
from typing import Dict, Any, List, Optional
from langchain_core.documents import Document

from agent.llm_provider import LLMProvider

def get_llm(provider: Optional[str] = None, model: Optional[str] = None, config_path: str = "config.yaml", temperature: float = 0.0):
    llm_manager = LLMProvider(provider=provider, model=model, config_path=config_path)
    if temperature != 0.0:
        llm_manager.llm.temperature = temperature
    return llm_manager.llm

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

async def _process_single_question(question: str, vectorstore, llm, semaphore: asyncio.Semaphore = None):
    results = {}
    
    retrieved_docs = vectorstore.similarity_search(question, k=15)
    
    docs_by_file = {}
    for doc in retrieved_docs:
        fname = doc.metadata.get("file_name", "Inconnu")
        if fname not in docs_by_file:
            docs_by_file[fname] = []
        docs_by_file[fname].append(doc)
    
    for fname, docs in docs_by_file.items():
        if fname == "dummy":
            continue
            
        context_text = "\n\n".join(
            [f"--- Extrait {i+1} (Page {doc.metadata.get('page', 'Inconnue')}) ---\n{doc.page_content}" 
             for i, doc in enumerate(docs[:2])]
        )
        
        # HARD LIMIT: Tronquer le contexte
        if len(context_text) > 4000:
            context_text = context_text[:4000] + "\n...[Tronqué]"
        
        prompt_str = f"""Tu es un expert en analyse de documents.
Ta mission est de répondre à la question suivante en te basant UNIQUEMENT sur le contexte fourni.
Si l'information n'est pas présente dans le contexte, tu DOIS répondre "NON_TROUVE". Ne devine rien.

Question : {question}

Contexte extrait du fichier {fname} :
{context_text}

Règles de formatage :
1. Donne une réponse claire et concise.
2. Si tu as trouvé l'information, indique le numéro de la page source entre crochets à la fin de ta réponse (ex: [Page 12]).
"""
        try:
            if semaphore:
                async with semaphore:
                    response = await _safe_ainvoke(llm, prompt_str)
            else:
                response = await _safe_ainvoke(llm, prompt_str)
                
            response = response.content.strip()
            
            if response == "NON_TROUVE" or response == "" or "NON_TROUVE" in response:
                results[fname] = {
                    "valeur": None,
                    "source": None,
                    "confiance": 0.0
                }
            else:
                page_num = None
                if "[Page " in response:
                    try:
                        page_str = response.split("[Page ")[1].split("]")[0]
                        page_num = int(page_str)
                        response = response.split("[Page ")[0].strip()
                    except:
                        pass
                        
                results[fname] = {
                    "valeur": response,
                    "source": {
                        "fichier": fname,
                        "page": page_num,
                        "extrait": context_text[:200] + "..."
                    },
                    "confiance": 0.85
                }
        except Exception as e:
            print(f"Erreur d'extraction multi pour le fichier {fname}, question '{question}': {e}")
            results[fname] = {"valeur": None, "source": None, "confiance": 0.0}
    
    return question, results

async def run_multi_extraction(
    vectorstore,
    questions: List[str],
    provider: Optional[str] = None,
    model: Optional[str] = None,
    config_path: str = "config.yaml",
) -> Dict[str, Any]:
    llm = get_llm(provider=provider, model=model, config_path=config_path)
    
    results_by_doc = {}
    
    # Création d'un sémaphore pour limiter la concurrence (Rate Limit)
    concurrency_limit = 1
    semaphore = asyncio.Semaphore(concurrency_limit)
    
    # ✅ SÉQUENTIEL : Traiter toutes les questions une par une
    question_results = []
    for q in questions:
        res = await _process_single_question(q, vectorstore, llm, semaphore)
        question_results.append(res)
    
    # Fusionner les résultats
    for question, doc_results in question_results:
        for fname, value in doc_results.items():
            if fname not in results_by_doc:
                results_by_doc[fname] = {}
            results_by_doc[fname][question] = value

    # Remplir les questions manquantes pour les documents qui n'ont pas eu de résultats dans la recherche vectorielle
    all_files = set()
    for fname in results_by_doc.keys():
        if fname != "dummy":
            all_files.add(fname)
            
    # Si le document est vide, s'assurer que all_files récupère bien les documents à partir du vectorstore
    if not all_files:
        try:
            # Récupérer tous les fichiers depuis le vectorstore (via une recherche générique)
            all_docs = vectorstore.similarity_search(" ", k=100)
            for doc in all_docs:
                fname = doc.metadata.get("file_name")
                if fname and fname != "dummy":
                    all_files.add(fname)
        except Exception:
            pass

    for fname in all_files:
        if fname not in results_by_doc:
            results_by_doc[fname] = {}
        for q in questions:
            if q not in results_by_doc[fname]:
                results_by_doc[fname][q] = {"valeur": None, "source": None, "confiance": 0.0}

    # Nettoyer l'index dummy s'il s'est glissé dans les résultats
    if "dummy" in results_by_doc:
        del results_by_doc["dummy"]

    # Maintenant, générer une synthèse comparative finale si plus d'un doc
    synthese = None
    if len(results_by_doc) > 1:
        synth_prompt = f"""Tu es un analyste stratégique. Voici les réponses obtenues à partir de plusieurs documents pour les questions suivantes :
{list(questions)}

Résultats par document :
"""
        for fname, q_res in results_by_doc.items():
            synth_prompt += f"\n- Document: {fname}\n"
            for q, res in q_res.items():
                val = res['valeur'] if res['valeur'] else 'Non trouvé'
                synth_prompt += f"  * {q} : {val}\n"
                
        synth_prompt += "\nFais une synthèse comparative courte (2-3 paragraphes) mettant en évidence les similitudes et différences entre ces documents."
        
        try:
            synthese = (await _safe_ainvoke(llm, synth_prompt)).content.strip()
        except:
            synthese = "Erreur lors de la génération de la synthèse."

    return {
        "results_by_document": results_by_doc,
        "synthese_comparative": synthese
    }
