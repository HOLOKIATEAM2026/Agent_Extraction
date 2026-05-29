import os
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

from langchain_core.prompts import PromptTemplate
from agent.llm_manager import get_llm

class DocumentCategories(BaseModel):
    """Modèle Pydantic pour forcer le LLM à répondre avec un format précis lors du routing"""
    is_strategique: bool = Field(description="Le document contient-il des informations sur la stratégie de l'entreprise (marché, concurrents, tendances) ?")
    is_financier: bool = Field(description="Le document contient-il des données financières (chiffre d'affaires, résultat net, EBITDA) ?")
    is_rh: bool = Field(description="Le document contient-il des informations sur les ressources humaines (effectifs, masse salariale) ?")
    is_data: bool = Field(description="Le document parle-t-il de la gestion des données, de leur qualité, architecture ou gouvernance ?")
    is_cyber: bool = Field(description="Le document aborde-t-il la cybersécurité, les risques informatiques ou la conformité NIST/ISO ?")
    
    def get_active_categories(self) -> List[str]:
        """Retourne la liste des catégories détectées comme 'True'"""
        active = []
        if self.is_strategique: active.append("strategique")
        if self.is_financier: active.append("financier")
        if self.is_rh: active.append("rh")
        if self.is_data: active.append("data")
        if self.is_cyber: active.append("cyber")
        return active


def get_document_preview(file_path: str, max_pages: int = 5) -> str:
    """
    Extrait les premières pages d'un document pour donner un aperçu au LLM.
    C'est généralement suffisant pour analyser le sommaire et l'introduction.
    """
    ext = os.path.splitext(file_path)[1].lower()
    text_preview = ""
    
    try:
        if ext == ".pdf":
            import fitz
            doc = fitz.open(file_path)
            pages_to_read = min(max_pages, len(doc))
            for i in range(pages_to_read):
                text_preview += doc[i].get_text("text") + "\n"
                
        elif ext == ".docx":
            import docx
            doc = docx.Document(file_path)
            # On prend approximativement les X premiers paragraphes (ex: 50 paragraphes ~ 3-4 pages)
            paras = [p.text for p in doc.paragraphs if p.text.strip()]
            text_preview = "\n".join(paras[:100])
            
        elif ext == ".txt":
            with open(file_path, "r", encoding="utf-8") as f:
                # Lire les 10000 premiers caractères
                text_preview = f.read(10000)
    except Exception as e:
        print(f"Erreur lors de la lecture de l'aperçu du fichier {file_path}: {e}")
        
    return text_preview


def analyze_document_type(
    file_path: str, 
    provider: Optional[str] = None, 
    model: Optional[str] = None,
    config_path: str = "config.yaml"
) -> DocumentCategories:
    """
    Analyse les premières pages du document pour déterminer de quoi il parle.
    Permet d'éviter de poser des questions hors-sujet au RAG.
    """
    # 1. Extraire le début du document (Sommaire, Intro...)
    preview = get_document_preview(file_path, max_pages=6)
    
    if not preview.strip():
        # Fallback si on n'a pas pu lire le document (on active tout par défaut pour ne rien rater)
        return DocumentCategories(is_strategique=True, is_financier=True, is_rh=True, is_data=True, is_cyber=True)

    # 2. Préparer le LLM structuré
    llm = get_llm(provider=provider, model=model, config_path=config_path, temperature=0.0)
    
    try:
        # Tenter d'utiliser with_structured_output (fonctionne bien avec OpenAI/Groq)
        structured_llm = llm.with_structured_output(DocumentCategories)
        
        prompt = PromptTemplate.from_template(
            "Tu es un analyste de documents d'entreprise.\n"
            "Analyse l'aperçu de ce document (qui contient le début et le sommaire) et détermine "
            "quelles thématiques sont abordées.\n\n"
            "Aperçu du document :\n{preview}\n\n"
            "Détermine si les catégories suivantes sont présentes : Stratégie, Finance, RH, Data, Cybersécurité."
        )
        
        chain = prompt | structured_llm
        result = chain.invoke({"preview": preview[:8000]}) # Limiter la taille pour ne pas exploser le prompt
        return result
        
    except Exception as e:
        print(f"[Analyzer] Erreur avec structured_output: {e}. Fallback vers tout actif.")
        # Si le modèle ne supporte pas structured_output (ex: certains modèles Ollama locaux),
        # on retourne True partout par sécurité.
        return DocumentCategories(is_strategique=True, is_financier=True, is_rh=True, is_data=True, is_cyber=True)
