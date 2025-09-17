#!/usr/bin/env python3
"""
Test des URLs ML
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.dev')
django.setup()

from django.urls import reverse
from django.test import Client

def test_urls():
    """Test des URLs ML"""
    print("🔍 Test des URLs ML...")
    
    client = Client()
    
    # Test de l'index status
    try:
        response = client.get('/api/v1/index/status/')
        print(f"✅ Index status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   - Index produits: {data['product_index']['exists']}")
    except Exception as e:
        print(f"❌ Erreur index status: {e}")
    
    # Test de la recherche
    try:
        response = client.get('/api/v1/search/?q=ordinateur&k=3')
        print(f"✅ Recherche: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   - Résultats: {data.get('count', 0)}")
        else:
            print(f"   - Erreur: {response.content}")
    except Exception as e:
        print(f"❌ Erreur recherche: {e}")
    
    # Test des recommandations
    try:
        response = client.get('/api/v1/products/1/recommendations/?k=3')
        print(f"✅ Recommandations: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   - Recommandations: {data.get('count', 0)}")
        else:
            print(f"   - Erreur: {response.content}")
    except Exception as e:
        print(f"❌ Erreur recommandations: {e}")

if __name__ == "__main__":
    test_urls()
