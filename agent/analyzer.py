import os
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

from langchain_core.prompts import PromptTemplate
from agent.llm_provider import LLMProvider

def get_llm(provider: Optional[str] = None, model: Optional[str] = None, config_path: str = "config.yaml", temperature: float = 0.0):
    llm_manager = LLMProvider(provider=provider, model=model, config_path=config_path)
    if temperature != 0.0:
        llm_manager.llm.temperature = temperature
    return llm_manager.llm

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


def get_document_preview(file_path: str, max_pages: int = 6) -> str:
    """
    Extrait les premières pages d'un document pour donner un aperçu au LLM.
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
            paras = [p.text for p in doc.paragraphs if p.text.strip()]
            text_preview = "\n".join(paras[:200])
            
        elif ext in (".txt", ".md"):
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text_preview = f.read(30000)
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
    ✅ ROUTING ULTRA-RAPIDE :
    1. Heuristique mots-clés (0 ms) — utilisée DIRECTEMENT 90% du temps
    2. LLM structured_output — SEULEMENT si heuristique ambiguë
    """
    preview = get_document_preview(file_path, max_pages=6)
    
    if not preview.strip():
        return DocumentCategories(is_strategique=True, is_financier=True, is_rh=True, is_data=True, is_cyber=True)

    lower = preview.lower()
    heuristique = {
        "strategique": any(k in lower for k in ["marché", "concurrent", "stratégie", "tendance", "secteur", "positionnement", "croissance du marché", "environnement concurrentiel", "offensive", "développement"]),
        "financier": any(k in lower for k in ["chiffre d'affaires", "résultat net", "ebitda", "bilan", "compte de résultat", "revenus", "bénéfice", "perte", "cac", "ca ", "performance économique", "marge", "roa", "roe"]),
        "rh": any(k in lower for k in ["effectif", "employé", "collaborateur", "masse salariale", "ressources humaines", "rh ", "personnel", "turnover", "recrutement", "formation", "santé au travail", "kpi rh", "salaire moyen", "absentéisme", "ressources humaine"]),
        "data": any(k in lower for k in ["données", "data ", "base de données", "data warehouse", "data lake", "gouvernance des données", "qualité des données", "bi ", "business intelligence", "analytics", "big data", "données personnelles", "catalog de donnée", "catalogue de données", "data lakehouse", "donnéees", "data warehouse"]),
        "cyber": any(k in lower for k in ["cybersécurité", "sécurité informatique", "nist", "iso 27001", "risque informatique", "cyber ", "rgpd", "protection des données", "ciso", "dpo", "incident de sécurité", "menace", "vulnérabilité", "hameçonnage", "phishing", "waf", "3d secure", "cyber"])
    }

    all_true = all(heuristique.values())
    any_true = any(heuristique.values())
    cat_count = sum(1 for v in heuristique.values() if v)
    is_ambiguous = (not any_true) or (cat_count <= 1 and not heuristique["financier"])

    if heuristique["financier"] and heuristique["strategique"] and cat_count >= 2:
        heuristique["rh"] = True
        heuristique["data"] = True
        heuristique["cyber"] = True

    if not is_ambiguous:
        print(f"[Analyzer] Routing par HEURISTIQUE (0s LLM) : {[k for k,v in heuristique.items() if v]}")
        return DocumentCategories(
            is_strategique=heuristique["strategique"] or heuristique["financier"],
            is_financier=heuristique["financier"],
            is_rh=heuristique["rh"],
            is_data=heuristique["data"],
            is_cyber=heuristique["cyber"]
        )

    llm = get_llm(provider=provider, model=model, config_path=config_path, temperature=0.0)
    
    try:
        structured_llm = llm.with_structured_output(DocumentCategories)
        prompt = PromptTemplate.from_template(
            "Analyse document entreprise. Quelles catégories présentes ?\n\n"
            "Extrait :\n{preview}"
        )
        chain = prompt | structured_llm
        result = chain.invoke({"preview": preview[:4000]})
        return result
    except Exception as e:
        print(f"[Analyzer] Erreur routing LLM: {e}. Heuristique sécuritaire.")
        return DocumentCategories(
            is_strategique=True,
            is_financier=heuristique["financier"] or True,
            is_rh=heuristique["rh"] or True,
            is_data=heuristique["data"] or True,
            is_cyber=heuristique["cyber"] or True
        )
