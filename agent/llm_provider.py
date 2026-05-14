import os
import yaml
from dotenv import load_dotenv

# Charger les variables d'environnement (ex: GROQ_API_KEY)
load_dotenv()

class LLMProvider:
    """
    Couche d'abstraction pour les modèles LLM.
    Permet de switcher entre Groq, Ollama, OpenAI, etc. avec une seule ligne de code.
    """
    
    def __init__(self, provider: str = None, model: str = None, config_path: str = "config.yaml"):
        # Charger la configuration depuis config.yaml
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Fichier de configuration introuvable: {config_path}")
            
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.provider = provider or self.config.get("default_provider", "groq")
        provider_config = self.config.get("providers", {}).get(self.provider, {})
        
        self.model_name = model or provider_config.get("model") or self.config.get("default_model")
        self.temperature = provider_config.get("temperature", 0.0)
        
        # Initialiser le modèle LangChain sous-jacent
        self.llm = self._initialize_llm(provider_config)

    def _initialize_llm(self, provider_config: dict):
        if self.provider == "groq":
            from langchain_groq import ChatGroq
            # Langchain_groq récupère automatiquement GROQ_API_KEY depuis l'environnement
            return ChatGroq(model_name=self.model_name, temperature=self.temperature)
            
        elif self.provider == "ollama":
            try:
                from langchain_ollama import ChatOllama
            except ImportError:
                # Fallback pour les anciennes versions de langchain
                from langchain_community.chat_models import ChatOllama
                
            base_url = provider_config.get("base_url", "http://localhost:11434")
            return ChatOllama(model=self.model_name, base_url=base_url, temperature=self.temperature)
            
        elif self.provider == "openai":
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(model=self.model_name, temperature=self.temperature)
            
        elif self.provider == "gemini":
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
            except ImportError as e:
                raise ImportError("Dépendance manquante: installez langchain-google-genai") from e
            return ChatGoogleGenerativeAI(model=self.model_name, temperature=self.temperature)
            
        else:
            raise ValueError(f"Provider LLM non supporté: {self.provider}")

    def complete(self, prompt: str) -> str:
        """
        Génère une réponse à partir du prompt donné.
        """
        response = self.llm.invoke(prompt)
        return response.content
