#!/usr/bin/env python3
"""
Script de test pour les endpoints ML
"""
import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def test_index_status():
    """Test du statut des index"""
    print("🔍 Test du statut des index...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/index/status/")
        if response.status_code == 200:
            data = response.json()
            print("✅ Statut des index:")
            print(f"   - Index produits: {data['product_index']['exists']} (v{data['product_index']['version']})")
            print(f"   - Index RAG: {data['rag_index']['exists']} (v{data['rag_index']['version']})")
            return True
        else:
            print(f"❌ Erreur: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_semantic_search():
    """Test de la recherche sémantique"""
    print("\n🔍 Test de la recherche sémantique...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/search/?q=ordinateur&k=3")
        if response.status_code == 200:
            data = response.json()
            print("✅ Recherche sémantique:")
            print(f"   - Requête: {data.get('query', 'N/A')}")
            print(f"   - Résultats: {data.get('count', 0)}")
            if data.get('results'):
                for i, result in enumerate(data['results'][:3], 1):
                    print(f"   - {i}. {result.get('name', 'N/A')} (score: {result.get('similarity_score', 0):.3f})")
            return True
        else:
            print(f"❌ Erreur: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_recommendations():
    """Test des recommandations"""
    print("\n🔍 Test des recommandations...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/products/1/recommendations/?k=3")
        if response.status_code == 200:
            data = response.json()
            print("✅ Recommandations:")
            print(f"   - Produit: {data.get('product_id', 'N/A')}")
            print(f"   - Recommandations: {data.get('count', 0)}")
            if data.get('recommendations'):
                for i, rec in enumerate(data['recommendations'][:3], 1):
                    print(f"   - {i}. {rec.get('name', 'N/A')} (score: {rec.get('similarity_score', 0):.3f})")
            return True
        else:
            print(f"❌ Erreur: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_rag_assistant():
    """Test de l'assistant RAG"""
    print("\n🔍 Test de l'assistant RAG...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/assistant/ask/",
            json={"question": "Comment passer une commande ?"},
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
            print(f"❌ Erreur: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def main():
    """Fonction principale"""
    print("🚀 Test des endpoints ML de SmartMarket")
    print("=" * 50)
    
    tests = [
        test_index_status,
        test_semantic_search,
        test_recommendations,
        test_rag_assistant
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Résultats: {passed}/{total} tests réussis")
    
    if passed == total:
        print("🎉 Tous les tests sont passés !")
        return 0
    else:
        print("⚠️  Certains tests ont échoué.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
