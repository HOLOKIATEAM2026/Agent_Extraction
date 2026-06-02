import json
import re
from typing import List, Dict, Any, Tuple
from langchain_core.vectorstores import VectorStore
from langchain_core.prompts import PromptTemplate
from agent.llm_config import get_llm

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
    
    # 2. Recherche des documents pertinents
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
    docs = retriever.invoke(message)
    
    # Extraire les citations
    citations = []
    context_parts = []
    
    for i, doc in enumerate(docs, 1):
        page = doc.metadata.get("page", "Inconnue")
        file_name = doc.metadata.get("file_name", "Inconnu")
        text = doc.page_content.strip()
        
        citations.append({
            "id": i,
            "page": page,
            "file_name": file_name,
            "extrait": text[:200] + "..." if len(text) > 200 else text
        })
        
        context_parts.append(f"--- Document {i} (Fichier: {file_name}, Page: {page}) ---\n{text}")
        
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
2. Cite toujours tes sources en te référant aux numéros de documents (ex: "D'après le Document 1...").
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
    
    llm = get_llm(provider=provider, model_name=model, temperature=0.0)
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
