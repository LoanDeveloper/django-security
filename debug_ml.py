#!/usr/bin/env python3
"""
Script de debug pour le module ML
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.dev')
django.setup()

from ml.index_manager import ProductIndexManager, RAGIndexManager
from catalog.models import Product

def test_product_index():
    """Test de l'index des produits"""
    print("🔍 Test de l'index des produits...")
    try:
        manager = ProductIndexManager()
        if manager.load_index():
            print("✅ Index des produits chargé")
            
            # Récupérer les produits
            products = {}
            for product in Product.objects.filter(is_active=True, stock__gt=0):
                products[product.id] = {
                    'id': product.id,
                    'name': product.name,
                    'description': '',
                    'category': product.category.name if product.category else '',
                    'price': float(product.price),
                    'is_active': product.is_active,
                    'stock_quantity': product.stock
                }
            
            print(f"✅ {len(products)} produits récupérés")
            
            # Test des recommandations
            recommendations = manager.get_recommendations(1, 3, products)
            print(f"✅ Recommandations pour le produit 1: {len(recommendations)}")
            for rec in recommendations:
                print(f"   - {rec['name']} (score: {rec['similarity_score']:.3f})")
            
            # Test de recherche
            search_results = manager.search_products("ordinateur", 3, products)
            print(f"✅ Recherche 'ordinateur': {len(search_results)} résultats")
            for result in search_results:
                print(f"   - {result['name']} (score: {result['similarity_score']:.3f})")
                
        else:
            print("❌ Impossible de charger l'index des produits")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

def test_rag_index():
    """Test de l'index RAG"""
    print("\n🔍 Test de l'index RAG...")
    try:
        manager = RAGIndexManager()
        if manager.load_index():
            print("✅ Index RAG chargé")
            
            # Test de question
            response = manager.ask_question("Comment passer une commande ?")
            print(f"✅ Réponse RAG: {response['answer'][:100]}...")
            print(f"   - Confiance: {response['confidence']:.3f}")
            print(f"   - Sources: {len(response['sources'])}")
            
        else:
            print("❌ Impossible de charger l'index RAG")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Fonction principale"""
    print("🚀 Debug du module ML")
    print("=" * 50)
    
    test_product_index()
    test_rag_index()

if __name__ == "__main__":
    main()
