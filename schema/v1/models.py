from typing import List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field


class SourceInfo(BaseModel):
    page: Optional[int] = Field(None, description="Numéro de la page source")
    section: Optional[str] = Field(None, description="Titre de la section ou du paragraphe")
    extrait: Optional[str] = Field(None, description="Extrait textuel exact du document justifiant la valeur")


class ExtractedField(BaseModel):
    valeur: Optional[Union[str, int, float, bool]] = Field(None, description="La valeur extraite")
    source: Optional[SourceInfo] = Field(None, description="La source exacte dans le document")
    confiance: float = Field(0.0, ge=0.0, le=1.0, description="Score de confiance entre 0.0 et 1.0")


class ExtractedListField(BaseModel):
    valeur: Optional[List[str]] = Field(default_factory=list, description="Liste de valeurs extraites")
    source: Optional[SourceInfo] = Field(None, description="La source exacte dans le document")
    confiance: float = Field(0.0, ge=0.0, le=1.0, description="Score de confiance entre 0.0 et 1.0")


class MetaInfo(BaseModel):
    entreprise: Optional[str] = None
    annee_rapport: Optional[int] = None
    date_extraction: Optional[datetime] = None
    modele_utilise: Optional[str] = None
    provider: Optional[str] = None
    approche: Optional[str] = None
    source_file: Optional[str] = None


class DiagnosticStrategique(BaseModel):
    taille_marche: ExtractedField = Field(default_factory=ExtractedField)
    taux_croissance: ExtractedField = Field(default_factory=ExtractedField)
    intensite_concurrentielle: ExtractedField = Field(default_factory=ExtractedField)
    concurrents: ExtractedListField = Field(default_factory=ExtractedListField)
    tendances_marche: ExtractedListField = Field(default_factory=ExtractedListField)


class DiagnosticFinancier(BaseModel):
    chiffre_affaires: ExtractedField = Field(default_factory=ExtractedField)
    resultat_net: ExtractedField = Field(default_factory=ExtractedField)
    ebitda: ExtractedField = Field(default_factory=ExtractedField)


class DiagnosticRH(BaseModel):
    effectif_total: ExtractedField = Field(default_factory=ExtractedField)
    masse_salariale: ExtractedField = Field(default_factory=ExtractedField)


class DiagnosticData(BaseModel):
    existence_donnees: ExtractedField = Field(default_factory=ExtractedField)
    qualite: ExtractedField = Field(default_factory=ExtractedField)
    accessibilite: ExtractedField = Field(default_factory=ExtractedField)
    volumetrie: ExtractedField = Field(default_factory=ExtractedField)
    historisation: ExtractedField = Field(default_factory=ExtractedField)
    conformite: ExtractedField = Field(default_factory=ExtractedField)
    documentation: ExtractedField = Field(default_factory=ExtractedField)


class DiagnosticCyberGouvernance(BaseModel):
    risques_identifies: ExtractedListField = Field(default_factory=ExtractedListField)
    conformite_nist: ExtractedField = Field(default_factory=ExtractedField)
    gouvernance_data: ExtractedField = Field(default_factory=ExtractedField)


class CopilotExtraction(BaseModel):
    """
    Modèle racine pour l'extraction de données du Copilot Holokia.
    Ce modèle garantit que la réponse LLM respectera toujours ce format.
    """
    meta: MetaInfo = Field(default_factory=MetaInfo)
    diagnostic_strategique: DiagnosticStrategique = Field(default_factory=DiagnosticStrategique)
    diagnostic_financier: DiagnosticFinancier = Field(default_factory=DiagnosticFinancier)
    diagnostic_rh: DiagnosticRH = Field(default_factory=DiagnosticRH)
    diagnostic_data: DiagnosticData = Field(default_factory=DiagnosticData)
    diagnostic_cyber_gouvernance: DiagnosticCyberGouvernance = Field(default_factory=DiagnosticCyberGouvernance)
