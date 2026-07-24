import json
import re
from typing import List, Dict, Any, Tuple
from langchain_core.vectorstores import VectorStore
from langchain_core.prompts import PromptTemplate
from agent.llm_provider import LLMProvider

def get_llm(provider: str = None, model: str = None, config_path: str = "config.yaml", temperature: float = 0.0):
    llm_manager = LLMProvider(provider=provider, model=model, config_path=config_path)
    if temperature != 0.0:
        llm_manager.llm.temperature = temperature
    return llm_manager.llm

def run_chat_rag(
    vectorstore: VectorStore,
    message: str,
    history: List[Dict[str, str]],
    provider: str,
    model: str
) -> Dict[str, Any]:
    """
    Exécute un pipeline RAG conversationnel.
    """
    # 1. Reformuler la question avec l'historique (optionnel mais recommandé)
    # Pour simplifier et économiser les tokens, on va injecter l'historique dans le prompt final.
    
    def _expand_query(q: str) -> List[str]:
        base = (q or "").strip()
        if not base:
            return []
        low = base.lower()
        expanded: List[str] = [base]

        if "chiffre" in low and ("affaire" in low or "affaires" in low or "ca" in low):
            expanded.append(base + " (chiffre d'affaires CA revenu revenus ventes)")
        if "effectif" in low or "employ" in low or "salari" in low:
            expanded.append(base + " (effectif employés salariés headcount)")
        if "résultat" in low or "resultat" in low or "bénéfice" in low or "benefice" in low:
            expanded.append(base + " (résultat net bénéfice profit)")

        uniq: List[str] = []
        seen = set()
        for x in expanded:
            if x not in seen:
                uniq.append(x)
                seen.add(x)
        return uniq[:3]

    def _doc_key(d) -> str:
        try:
            return (
                str(d.metadata.get("file_name") or "")
                + "|"
                + str(d.metadata.get("page") or d.metadata.get("pages") or "")
                + "|"
                + str(hash(d.page_content or ""))
            )
        except Exception:
            return str(id(d))

    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
    docs: List[Any] = []
    seen_docs = set()
    for q in _expand_query(message):
        try:
            cur = retriever.invoke(q)
        except Exception:
            continue
        for d in cur or []:
            k = _doc_key(d)
            if k in seen_docs:
                continue
            docs.append(d)
            seen_docs.add(k)
            if len(docs) >= 8:
                break
        if len(docs) >= 8:
            break
    
    # Extraire les citations
    citations = []
    context_parts = []
    
    # Map to track actual document index provided to the LLM
    doc_index_map = {}
    
    for i, doc in enumerate(docs, 1):
        page = doc.metadata.get("page", "Inconnue")
        file_name = doc.metadata.get("file_name", "Inconnu")
        text = doc.page_content.strip()
        
        # Determine the visual document ID for the LLM
        doc_key = f"{file_name}_p{page}"
        if doc_key not in doc_index_map:
            doc_index_map[doc_key] = len(doc_index_map) + 1
            
        doc_id = doc_index_map[doc_key]
        
        # Deduplicate citations that point to the exact same file and page
        citation_exists = False
        for c in citations:
            if c["file_name"] == file_name and c["page"] == page:
                citation_exists = True
                break
                
        if not citation_exists:
            citations.append({
                "page": page,
                "file_name": file_name,
                "extrait": text[:200] + "..." if len(text) > 200 else text
            })
        
        context_parts.append(f"--- Extrait de {file_name}, Page {page} ---\n{text}")
        
    context_str = "\n\n".join(context_parts)
    
    # Formater l'historique
    history_str = ""
    if history:
        history_str = "Historique de la conversation :\n"
        for msg in history[-4:]: # Garder les 4 derniers messages max
            role = "Utilisateur" if msg.get("role") == "user" else "Assistant"
            history_str += f"{role}: {msg.get('content')}\n"
    
    # 3. Prompt RAG
    prompt_template = """Tu es un assistant IA expert dans l'analyse de documents d'entreprise.
Ton but est de répondre à la question de l'utilisateur de manière précise, claire et professionnelle, UNIQUEMENT en te basant sur le contexte fourni.

RÈGLES IMPORTANTES :
1. Si la réponse ne se trouve PAS dans le contexte, dis simplement "Je ne trouve pas cette information dans les documents fournis." N'invente jamais d'informations.
2. Cite toujours tes sources en te référant au nom du fichier et au numéro de page (ex: "D'après test.txt, page 4...").
3. Prends en compte l'historique de la conversation si nécessaire pour comprendre le contexte de la question.

{history}

CONTEXTE EXTRAIT DES DOCUMENTS :
{context}

QUESTION DE L'UTILISATEUR :
{question}

RÉPONSE :"""

    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["history", "context", "question"]
    )
    
    llm = get_llm(provider=provider, model=model, temperature=0.0)
    chain = prompt | llm
    
    response_text = chain.invoke({
        "history": history_str,
        "context": context_str,
        "question": message
    })
    
    # Nettoyer la réponse (si c'est un objet AIMessage)
    if hasattr(response_text, "content"):
        response_text = response_text.content
        
    return {
        "answer": response_text.strip(),
        "citations": citations
    }
