import json
import tempfile
import os
from django.test import TestCase, Client
from django.urls import reverse
from django.core.cache import cache
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch, MagicMock

from .models import IndexManifest, SearchLog
from .index_manager import ProductIndexManager, RAGIndexManager
from .preprocessing.text_processor import TextProcessor
from .vectorization.tfidf_vectorizer import TFIDFVectorizer
from .rag.document_processor import DocumentProcessor
from .cache_manager import CacheManager
from catalog.models import Product


class TextProcessorTestCase(TestCase):
    """Tests pour le processeur de texte"""
    
    def setUp(self):
        self.processor = TextProcessor()
    
    def test_clean_text(self):
        """Test du nettoyage de texte"""
        text = "Bonjour ! Comment allez-vous ? 123"
        cleaned = self.processor.clean_text(text)
        self.assertEqual(cleaned, "bonjour comment allez vous")
    
    def test_process_text(self):
        """Test du pipeline complet de traitement"""
        text = "Les produits électroniques sont très populaires"
        processed = self.processor.process_text(text)
        self.assertIsInstance(processed, str)
        self.assertGreater(len(processed), 0)
    
    def test_extract_keywords(self):
        """Test de l'extraction de mots-clés"""
        text = "ordinateur portable gaming performance"
        keywords = self.processor.extract_keywords(text, max_keywords=3)
        self.assertIsInstance(keywords, list)
        self.assertLessEqual(len(keywords), 3)


class TFIDFVectorizerTestCase(TestCase):
    """Tests pour le vectoriseur TF-IDF"""
    
    def setUp(self):
        self.vectorizer = TFIDFVectorizer(max_features=100)
        self.texts = [
            "ordinateur portable gaming",
            "smartphone android",
            "ordinateur portable professionnel",
            "tablette android"
        ]
    
    def test_fit_transform(self):
        """Test de l'entraînement et de la transformation"""
        vectors = self.vectorizer.fit_transform(self.texts)
        self.assertEqual(vectors.shape[0], len(self.texts))
        self.assertEqual(vectors.shape[1], self.vectorizer.vectorizer.max_features)
    
    def test_similarity_computation(self):
        """Test du calcul de similarité"""
        self.vectorizer.fit(self.texts)
        query_vector = self.vectorizer.transform(["ordinateur portable"])
        similarities = self.vectorizer.compute_similarity(
            query_vector[0], 
            self.vectorizer.transform(self.texts)
        )
        self.assertEqual(len(similarities), len(self.texts))
        self.assertTrue(all(0 <= sim <= 1 for sim in similarities))
    
    def test_save_load(self):
        """Test de sauvegarde et chargement"""
        self.vectorizer.fit(self.texts)
        
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            filepath = tmp_file.name
        
        try:
            # Sauvegarder
            self.vectorizer.save(filepath)
            
            # Charger
            loaded_vectorizer = TFIDFVectorizer.load(filepath)
            
            # Vérifier que les features sont identiques
            self.assertEqual(
                len(self.vectorizer.feature_names),
                len(loaded_vectorizer.feature_names)
            )
            
        finally:
            if os.path.exists(filepath):
                os.unlink(filepath)


class DocumentProcessorTestCase(TestCase):
    """Tests pour le processeur de documents"""
    
    def setUp(self):
        self.processor = DocumentProcessor(chunk_size=100, chunk_overlap=20)
    
    def test_chunk_text(self):
        """Test du découpage de texte"""
        text = "Ceci est un long texte qui doit être découpé en plusieurs chunks pour le traitement."
        chunks = self.processor.chunk_text(text)
        
        self.assertIsInstance(chunks, list)
        self.assertGreater(len(chunks), 0)
        
        for chunk in chunks:
            self.assertIsInstance(chunk.id, str)
            self.assertIsInstance(chunk.content, str)
            self.assertIsInstance(chunk.metadata, dict)
    
    def test_process_faq_documents(self):
        """Test du traitement des documents FAQ"""
        faq_data = [
            {
                'question': 'Comment passer une commande ?',
                'answer': 'Ajoutez les produits au panier et suivez le checkout.',
                'category': 'commande'
            }
        ]
        
        chunks = self.processor.process_faq_documents(faq_data)
        self.assertGreater(len(chunks), 0)
        
        for chunk in chunks:
            self.assertEqual(chunk.metadata['type'], 'faq')


class CacheManagerTestCase(TestCase):
    """Tests pour le gestionnaire de cache"""
    
    def setUp(self):
        self.cache_manager = CacheManager()
        cache.clear()
    
    def test_recommendations_cache(self):
        """Test du cache des recommandations"""
        product_id = 1
        recommendations = [{'product_id': 2, 'score': 0.8}]
        
        # Mettre en cache
        result = self.cache_manager.set_recommendations(product_id, recommendations)
        self.assertTrue(result)
        
        # Récupérer du cache
        cached = self.cache_manager.get_recommendations(product_id)
        self.assertEqual(cached, recommendations)
    
    def test_search_cache(self):
        """Test du cache des recherches"""
        query = "ordinateur portable"
        results = [{'product_id': 1, 'score': 0.9}]
        
        # Mettre en cache
        result = self.cache_manager.set_search_results(query, results)
        self.assertTrue(result)
        
        # Récupérer du cache
        cached = self.cache_manager.get_search_results(query)
        self.assertEqual(cached, results)


class MLAPITestCase(APITestCase):
    """Tests pour les API ML"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Créer des produits de test
        self.product1 = Product.objects.create(
            name='Ordinateur portable',
            description='Ordinateur portable gaming',
            category='Informatique',
            price=999.99,
            stock_quantity=10
        )
        
        self.product2 = Product.objects.create(
            name='Smartphone Android',
            description='Smartphone haut de gamme',
            category='Mobile',
            price=599.99,
            stock_quantity=5
        )
        
        # Vider le cache
        cache.clear()
    
    def test_product_recommendations_endpoint(self):
        """Test de l'endpoint des recommandations"""
        url = reverse('ml:product_recommendations', args=[self.product1.id])
        
        # Mock du ProductIndexManager
        with patch('ml.views.ProductIndexManager') as mock_manager:
            mock_instance = MagicMock()
            mock_instance.load_index.return_value = True
            mock_instance.get_recommendations.return_value = [
                {
                    'product_id': self.product2.id,
                    'name': self.product2.name,
                    'similarity_score': 0.8,
                    'explanation': 'Produit similaire'
                }
            ]
            mock_manager.return_value = mock_instance
            
            response = self.client.get(url)
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            data = response.json()
            self.assertIn('recommendations', data)
            self.assertIn('product_id', data)
    
    def test_semantic_search_endpoint(self):
        """Test de l'endpoint de recherche sémantique"""
        url = reverse('ml:semantic_search')
        
        # Mock du ProductIndexManager
        with patch('ml.views.ProductIndexManager') as mock_manager:
            mock_instance = MagicMock()
            mock_instance.load_index.return_value = True
            mock_instance.search_products.return_value = [
                {
                    'product_id': self.product1.id,
                    'name': self.product1.name,
                    'similarity_score': 0.9,
                    'reason': 'Correspondance forte'
                }
            ]
            mock_manager.return_value = mock_instance
            
            response = self.client.get(url, {'q': 'ordinateur'})
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            data = response.json()
            self.assertIn('results', data)
            self.assertIn('query', data)
    
    def test_assistant_ask_endpoint(self):
        """Test de l'endpoint de l'assistant"""
        url = reverse('ml:assistant_ask')
        
        # Mock du RAGIndexManager
        with patch('ml.views.RAGIndexManager') as mock_manager:
            mock_instance = MagicMock()
            mock_instance.load_index.return_value = True
            mock_instance.ask_question.return_value = {
                'answer': 'Voici la réponse',
                'sources': [{'content': 'Source 1'}],
                'confidence': 0.8,
                'trace_id': 'test-trace-id'
            }
            mock_manager.return_value = mock_instance
            
            response = self.client.post(url, {
                'question': 'Comment passer une commande ?'
            }, content_type='application/json')
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            data = response.json()
            self.assertIn('answer', data)
            self.assertIn('sources', data)
    
    def test_index_status_endpoint(self):
        """Test de l'endpoint de statut des index"""
        url = reverse('ml:index_status')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn('product_index', data)
        self.assertIn('rag_index', data)
    
    def test_search_without_query(self):
        """Test de recherche sans requête"""
        url = reverse('ml:semantic_search')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertIn('error', data)
    
    def test_assistant_without_question(self):
        """Test de l'assistant sans question"""
        url = reverse('ml:assistant_ask')
        
        response = self.client.post(url, {}, content_type='application/json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertIn('error', data)


class SearchLogTestCase(TestCase):
    """Tests pour le modèle SearchLog"""
    
    def test_create_search_log(self):
        """Test de création d'un log de recherche"""
        log = SearchLog.objects.create(
            trace_id='test-trace-id',
            query='test query',
            results_count=5,
            top_k_scores=[0.9, 0.8, 0.7],
            index_version='1.0.0',
            response_time_ms=100
        )
        
        self.assertEqual(log.query, 'test query')
        self.assertEqual(log.results_count, 5)
        self.assertEqual(len(log.top_k_scores), 3)


class IndexManifestTestCase(TestCase):
    """Tests pour le modèle IndexManifest"""
    
    def test_create_index_manifest(self):
        """Test de création d'un manifest d'index"""
        manifest = IndexManifest.objects.create(
            name='test_index',
            version='1.0.0',
            file_path='/tmp/test.pkl',
            metadata={'test': 'value'}
        )
        
        self.assertEqual(manifest.name, 'test_index')
        self.assertEqual(manifest.version, '1.0.0')
        self.assertEqual(manifest.metadata['test'], 'value')
