from typing import Dict, List, Any
from agent.analyzer import DocumentCategories

# -------------------------------------------------------------------------
# QUESTIONS DYNAMIQUES
# -------------------------------------------------------------------------
# Ce dictionnaire fait le lien entre une catégorie et les questions RAG exactes à poser.
# Si une catégorie n'est pas détectée par l'analyzer, ses questions ne seront JAMAIS posées au LLM.
# Cela économise énormément de tokens et évite les hallucinations.

QUESTIONS_PAR_CATEGORIE = {
    "strategique": [
        {
            "champ": "taille_marche",
            "question": "Quelle est la taille ou la valeur du marché sur lequel l'entreprise opère ?",
            "type": "field"
        },
        {
            "champ": "taux_croissance",
            "question": "Quel est le taux de croissance du marché ?",
            "type": "field"
        },
        {
            "champ": "intensite_concurrentielle",
            "question": "Comment l'entreprise décrit-elle l'intensité concurrentielle ou la concurrence ?",
            "type": "field"
        },
        {
            "champ": "concurrents",
            "question": "Quels sont les principaux concurrents cités par l'entreprise ?",
            "type": "list"
        },
        {
            "champ": "tendances_marche",
            "question": "Quelles sont les principales tendances du marché ou évolutions sectorielles mentionnées ?",
            "type": "list"
        }
    ],
    
    "financier": [
        {
            "champ": "chiffre_affaires",
            "question": "Quel est le chiffre d'affaires (revenus) total généré par l'entreprise ?",
            "type": "field"
        },
        {
            "champ": "resultat_net",
            "question": "Quel est le résultat net (bénéfice ou perte net) de l'entreprise ?",
            "type": "field"
        },
        {
            "champ": "ebitda",
            "question": "Quel est l'EBITDA (ou EBE - Excédent Brut d'Exploitation) de l'entreprise ?",
            "type": "field"
        }
    ],
    
    "rh": [
        {
            "champ": "effectif_total",
            "question": "Quel est l'effectif total (nombre d'employés ou de collaborateurs) de l'entreprise ?",
            "type": "field"
        },
        {
            "champ": "masse_salariale",
            "question": "Quelle est la masse salariale (ou frais de personnel) de l'entreprise ?",
            "type": "field"
        }
    ],
    
    "data": [
        {
            "champ": "existence_donnees",
            "question": "Le document mentionne-t-il l'existence de bases de données, d'entrepôts de données (data warehouse) ou de lacs de données (data lake) ?",
            "type": "field"
        },
        {
            "champ": "qualite",
            "question": "Quelles sont les informations sur la qualité des données (nettoyage, standardisation, intégrité) ?",
            "type": "field"
        },
        {
            "champ": "accessibilite",
            "question": "Comment les données sont-elles accessibles ? Y a-t-il des mentions de portails, d'API ou d'outils BI (Business Intelligence) ?",
            "type": "field"
        },
        {
            "champ": "volumetrie",
            "question": "Y a-t-il des indications sur la volumétrie (taille en To, Go) des données gérées ?",
            "type": "field"
        },
        {
            "champ": "historisation",
            "question": "Le document parle-t-il de l'historisation, de l'archivage ou de la durée de conservation des données ?",
            "type": "field"
        },
        {
            "champ": "conformite",
            "question": "Comment l'entreprise gère-t-il la conformité des données (RGPD, CNIL, protection des données personnelles) ?",
            "type": "field"
        },
        {
            "champ": "documentation",
            "question": "Existe-t-il un dictionnaire de données, un catalogue de données ou une documentation de l'architecture data ?",
            "type": "field"
        }
    ],
    
    "cyber": [
        {
            "champ": "risques_identifies",
            "question": "Quels sont les risques de cybersécurité ou risques informatiques explicitement identifiés ?",
            "type": "list"
        },
        {
            "champ": "conformite_nist",
            "question": "Y a-t-il des mentions de conformité à des standards de sécurité comme NIST, ISO 27001 ou autres frameworks cyber ?",
            "type": "field"
        },
        {
            "champ": "gouvernance_data",
            "question": "Comment s'organise la gouvernance des données (CISO, DPO, comités de sécurité, politiques de sécurité) ?",
            "type": "field"
        }
    ]
}


def get_all_questions() -> Dict[str, List[Dict[str, str]]]:
    """
    Récupère les questions depuis Supabase si disponible, sinon utilise le dictionnaire par défaut.
    """
    try:
        from agent.supabase_store import SupabaseStore, supabase_enabled
        if supabase_enabled():
            store = SupabaseStore()
            db_questions = store.get_custom_questions()
            if db_questions:
                q_dict = {}
                for row in db_questions:
                    cat = row.get("categorie")
                    if not cat:
                        continue
                    if cat not in q_dict:
                        q_dict[cat] = []
                    q_dict[cat].append({
                        "id": row.get("id"),
                        "champ": row.get("champ"),
                        "question": row.get("question_text"),
                        "type": row.get("type", "field")
                    })
                return q_dict
    except Exception:
        pass
    
    return QUESTIONS_PAR_CATEGORIE

def build_dynamic_queries(categories: DocumentCategories) -> Dict[str, List[Dict[str, str]]]:
    """
    Construit le dictionnaire final des requêtes RAG à exécuter,
    uniquement pour les catégories qui ont été détectées comme 'True' par l'Analyzer.
    """
    active_cats = categories.get_active_categories()
    all_questions = get_all_questions()
    
    queries_to_run = {}
    for cat in active_cats:
        if cat in all_questions:
            queries_to_run[cat] = all_questions[cat]
            
    return queries_to_run

def get_empty_category_result(category_name: str) -> Dict[str, Any]:
    """
    Si une catégorie est ignorée par l'analyzer, on renvoie ce dictionnaire 
    rempli de 'null' pour respecter le schéma JSON global sans faire d'appels LLM.
    """
    all_questions = get_all_questions()
    if category_name not in all_questions:
        return {}
        
    result = {}
    for q in all_questions[category_name]:
        champ = q["champ"]
        if q["type"] == "list":
            result[champ] = {"valeur": [], "source": None, "confiance": 0.0}
        else:
            result[champ] = {"valeur": None, "source": None, "confiance": 0.0}
            
    return result
