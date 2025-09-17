#!/usr/bin/env python3
"""
Test de l'assistant RAG avec authentification
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_rag_with_auth():
    """Test de l'assistant RAG avec authentification"""
    print("🔍 Test de l'assistant RAG avec authentification...")
    
    # Créer une session
    session = requests.Session()
    
    # Se connecter (utiliser l'utilisateur admin par défaut)
    login_data = {
        'username': 'admin',
        'password': 'admin123'
    }
    
    try:
        # Login
        response = session.post(f"{BASE_URL}/login/", data=login_data)
        if response.status_code == 200:
            print("✅ Connexion réussie")
            
            # Test de l'assistant RAG
            rag_data = {
                "question": "Comment passer une commande ?"
            }
            
            response = session.post(
                f"{BASE_URL}/api/v1/assistant/ask/",
                json=rag_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Assistant RAG:")
                print(f"   - Question: {data.get('question', 'N/A')}")
                print(f"   - Réponse: {data.get('answer', 'N/A')[:100]}...")
                print(f"   - Confiance: {data.get('confidence', 0):.3f}")
                print(f"   - Sources: {len(data.get('sources', []))}")
                return True
            else:
                print(f"❌ Erreur RAG: {response.status_code} - {response.text}")
                return False
        else:
            print(f"❌ Erreur de connexion: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

if __name__ == "__main__":
    test_rag_with_auth()
