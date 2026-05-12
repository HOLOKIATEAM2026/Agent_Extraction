from agent.llm_provider import LLMProvider

def test_providers():
    print("🚀 Début des tests des providers LLM...\n")
    
    # 1. Test de Groq (Cloud, très rapide)
    print("--- 🟢 Test GROQ ---")
    try:
        # On peut forcer un modèle pour que le test soit rapide
        llm_groq = LLMProvider(provider="groq", model="llama-3.1-8b-instant")
        print("Modèle initialisé avec succès.")
        
        response = llm_groq.complete("Bonjour, dis-moi juste 'Test Groq OK' et rien d'autre.")
        print(f"Réponse: {response}")
    except Exception as e:
        print(f"❌ Erreur avec Groq: {e}")
        
    print("\n-------------------------------------------------\n")

    # 2. Test de Ollama (Local)
    print("--- 🦙 Test OLLAMA (Local) ---")
    try:
        llm_ollama = LLMProvider(provider="ollama", model="mistral")
        print(f"Modèle initialisé avec succès (Base URL: http://localhost:11434).")
        
        response = llm_ollama.complete("Bonjour, dis-moi juste 'Test Ollama OK' et rien d'autre.")
        print(f"Réponse: {response}")
    except Exception as e:
        print(f"❌ Erreur avec Ollama (vérifiez `ollama serve` et `ollama list`): {e}")

if __name__ == "__main__":
    test_providers()
