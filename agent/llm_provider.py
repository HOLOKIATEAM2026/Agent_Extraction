import os
import yaml
import threading
import time
from typing import Any, Dict, Optional, Tuple
from dotenv import load_dotenv

load_dotenv()

_LLM_CACHE: Dict[Tuple[str, str, str, float], Any] = {}
_LLM_CACHE_LOCK = threading.Lock()


class LLMProvider:
    """
    Couche d'abstraction pour les modèles LLM.
    ✅ VERSION OPTIMISÉE : Mise en cache SINGLETON globale pour éviter
    de réinstancier le client LLM (et son handshake HTTP) à CHAQUE appel.
    """
    
    def __init__(self, provider: str = None, model: str = None, config_path: str = "config.yaml"):
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Fichier de configuration introuvable: {config_path}")
            
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.provider = provider or self.config.get("default_provider", "groq")
        provider_config = self.config.get("providers", {}).get(self.provider, {})
        
        self.model_name = model or provider_config.get("model") or self.config.get("default_model")
        self.temperature = provider_config.get("temperature", 0.0)

        cache_key = (self.provider, self.model_name, config_path, float(self.temperature))
        with _LLM_CACHE_LOCK:
            cached = _LLM_CACHE.get(cache_key)
            if cached is not None:
                self.llm = cached
                return

        raw_llm = self._initialize_llm(provider_config)
        with _LLM_CACHE_LOCK:
            _LLM_CACHE[cache_key] = raw_llm
        self.llm = raw_llm

    def _initialize_llm(self, provider_config: dict):
        if self.provider == "groq":
            from langchain_groq import ChatGroq
            return ChatGroq(
                model_name=self.model_name,
                temperature=self.temperature,
                max_retries=1,
                timeout=30,
            )
            
        elif self.provider == "ollama":
            try:
                from langchain_ollama import ChatOllama
            except ImportError:
                from langchain_community.chat_models import ChatOllama
                
            base_url = provider_config.get("base_url", "http://localhost:11434")
            return ChatOllama(
                model=self.model_name,
                base_url=base_url,
                temperature=self.temperature,
                num_predict=512,
            )
            
        elif self.provider == "openai":
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model=self.model_name,
                temperature=self.temperature,
                max_retries=1,
                timeout=30,
            )
            
        elif self.provider == "gemini":
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
            except ImportError as e:
                raise ImportError("Dépendance manquante: installez langchain-google-genai") from e
            return ChatGoogleGenerativeAI(
                model=self.model_name,
                temperature=self.temperature,
                max_retries=1,
                timeout=30,
            )
            
        else:
            raise ValueError(f"Provider LLM non supporté: {self.provider}")

    def complete(self, prompt: str) -> str:
        response = self.llm.invoke(prompt)
        return response.content
