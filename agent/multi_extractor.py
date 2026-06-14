import os
from typing import Dict, Any, List, Optional
from langchain_core.documents import Document

from agent.llm_provider import LLMProvider

def get_llm(provider: Optional[str] = None, model: Optional[str] = None, config_path: str = "config.yaml", temperature: float = 0.0):
    llm_manager = LLMProvider(provider=provider, model=model, config_path=config_path)
    if temperature != 0.0:
        llm_manager.llm.temperature = temperature
    return llm_manager.llm

def run_multi_extraction(
    vectorstore,
    questions: List[str],
    provider: Optional[str] = None,
    model: Optional[str] = None,
    config_path: str = "config.yaml",
) -> Dict[str, Any]:
    llm = get_llm(provider=provider, model=model, config_path=config_path)
    
    results_by_doc = {}
    
    # Pour chaque question
    for question in questions:
        # On fait un retrieval global
        retrieved_docs = vectorstore.similarity_search(question, k=15)
        
        # On groupe les docs par fichier source
        docs_by_file = {}
        for doc in retrieved_docs:
            fname = doc.metadata.get("file_name", "Inconnu")
            if fname not in docs_by_file:
                docs_by_file[fname] = []
            docs_by_file[fname].append(doc)
            
        # Pour chaque fichier trouvé, on pose la question au LLM
        for fname, docs in docs_by_file.items():
            if fname not in results_by_doc:
                results_by_doc[fname] = {}
                
            context_text = "\n\n".join(
                [f"--- Extrait {i+1} (Page {doc.metadata.get('page', 'Inconnue')}) ---\n{doc.page_content}" 
                 for i, doc in enumerate(docs[:3])]
            )
            
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
                response = llm.invoke(prompt_str).content.strip()
                
                if response == "NON_TROUVE" or response == "" or "NON_TROUVE" in response:
                    results_by_doc[fname][question] = {
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
                            
                    results_by_doc[fname][question] = {
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
                results_by_doc[fname][question] = {"valeur": None, "source": None, "confiance": 0.0}

    # Remplir les questions manquantes pour les documents qui n'ont pas eu de résultats dans la recherche vectorielle
    all_fnames = list(results_by_doc.keys())
    for fname in all_fnames:
        for q in questions:
            if q not in results_by_doc[fname]:
                results_by_doc[fname][q] = {"valeur": None, "source": None, "confiance": 0.0}

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
            synthese = (await llm.ainvoke(synth_prompt)).content.strip()
        except Exception as e:
            print(f"Erreur génération synthèse: {e}")
            synthese = "Erreur lors de la génération de la synthèse."

    return {
        "results_by_document": results_by_doc,
        "synthese_comparative": synthese
    }
