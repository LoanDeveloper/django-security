import os
import json
import pickle
from datetime import datetime
from typing import List, Dict, Any, Optional
from django.conf import settings
from django.db import transaction
from .models import IndexManifest
from .preprocessing.text_processor import ProductPreprocessor
from .vectorization.tfidf_vectorizer import ProductVectorizer
from .rag.document_processor import DocumentProcessor
from .rag.retrieval_system import RAGRetrievalSystem
from .cache_manager import IndexVersionManager
import logging

logger = logging.getLogger(__name__)


class ProductIndexManager:
    """Gestionnaire d'index pour les produits et recommandations"""
    
    def __init__(self):
        self.preprocessor = ProductPreprocessor()
        self.vectorizer = ProductVectorizer()
        self.version_manager = IndexVersionManager()
        self.index_dir = getattr(settings, 'ML_INDEX_DIR', 'ml_indexes')
        os.makedirs(self.index_dir, exist_ok=True)
    
    def build_index(self, products: List[Dict[str, Any]], 
                   force_rebuild: bool = False) -> str:
        """Construit l'index des produits"""
        try:
            # Vérifier si l'index existe déjà
            if not force_rebuild and self._index_exists():
                logger.info("Index already exists, skipping build")
                return self.version_manager.get_current_version()
            
            logger.info(f"Building product index with {len(products)} products")
            
            # Préprocesser les produits
            processed_products = []
            for product in products:
                processed = self.preprocessor.prepare_product_features(product)
                if processed.get('processed_text'):  # Seulement les produits avec du texte
                    processed_products.append(processed)
            
            if not processed_products:
                raise ValueError("No valid products to index")
            
            # Entraîner le vectoriseur
            self.vectorizer.fit_products(processed_products)
            
            # Sauvegarder l'index
            index_path = os.path.join(self.index_dir, 'product_index.pkl')
            self.vectorizer.save(index_path)
            
            # Créer le manifest
            version = self.version_manager.increment_version()
            manifest = IndexManifest.objects.create(
                name='product_index',
                version=version,
                file_path=index_path,
                metadata={
                    'product_count': len(processed_products),
                    'created_at': datetime.now().isoformat(),
                    'vectorizer_type': 'TF-IDF',
                    'max_features': self.vectorizer.tfidf.vectorizer.max_features
                }
            )
            
            logger.info(f"Product index built successfully: {version}")
            return version
            
        except Exception as e:
            logger.error(f"Error building product index: {e}")
            raise
    
    def load_index(self) -> bool:
        """Charge l'index depuis le disque"""
        try:
            # Récupérer le manifest le plus récent
            manifest = IndexManifest.objects.filter(name='product_index').first()
            if not manifest:
                logger.warning("No product index manifest found")
                return False
            
            # Charger l'index
            if os.path.exists(manifest.file_path):
                self.vectorizer = ProductVectorizer.load(manifest.file_path)
                logger.info(f"Product index loaded: {manifest.version}")
                return True
            else:
                logger.error(f"Index file not found: {manifest.file_path}")
                return False
                
        except Exception as e:
            logger.error(f"Error loading product index: {e}")
            return False
    
    def get_recommendations(self, product_id: int, k: int = 10, 
                          products: Dict[int, Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Rréupère les recommandations pour un produit"""
        if not self.vectorizer.is_ready():
            logger.warning("Product index not ready")
            return []
        
        try:
            # Obtenir les produits similaires
            similar_products = self.vectorizer.get_similar_products(product_id, k)
            
            if not similar_products:
                return []
            
            # Filtrer les produits actifs et en stock
            filtered_products = []
            for product_id, similarity in similar_products:
                if products and product_id in products:
                    product = products[product_id]
                    if product.get('is_active', True) and product.get('stock_quantity', 0) > 0:
                        filtered_products.append((product_id, similarity))
            
            # Construire la réponse
            recommendations = []
            for product_id, similarity in filtered_products[:k]:
                if products and product_id in products:
                    product = products[product_id]
                    recommendation = {
                        'product_id': product_id,
                        'name': product.get('name', ''),
                        'category': product.get('category', ''),
                        'price': product.get('price', 0),
                        'similarity_score': similarity,
                        'explanation': self._get_recommendation_explanation(
                            product_id, similarity, products
                        )
                    }
                    recommendations.append(recommendation)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting recommendations: {e}")
            return []
    
    def search_products(self, query: str, k: int = 20, 
                       products: Dict[int, Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Recherche des produits par similarité textuelle"""
        if not self.vectorizer.is_ready():
            logger.warning("Product index not ready")
            return []
        
        try:
            # Rechercher des produits similaires
            similar_products = self.vectorizer.search_products(query, k)
            
            if not similar_products:
                return []
            
            # Construire la réponse
            results = []
            for product_id, similarity in similar_products:
                if products and product_id in products:
                    product = products[product_id]
                    result = {
                        'product_id': product_id,
                        'name': product.get('name', ''),
                        'category': product.get('category', ''),
                        'price': product.get('price', 0),
                        'similarity_score': similarity,
                        'reason': f"Correspondance sur les caractéristiques (score: {similarity:.3f})"
                    }
                    results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching products: {e}")
            return []
    
    def _get_recommendation_explanation(self, product_id: int, similarity: float, 
                                      products: Dict[int, Dict[str, Any]]) -> str:
        """Génère une explication pour une recommandation"""
        if not products or product_id not in products:
            return f"Produit similaire (score: {similarity:.3f})"
        
        product = products[product_id]
        explanations = []
        
        if similarity > 0.8:
            explanations.append("Très similaire")
        elif similarity > 0.6:
            explanations.append("Similaire")
        else:
            explanations.append("Relativement similaire")
        
        if product.get('category'):
            explanations.append(f"Catégorie: {product['category']}")
        
        if product.get('price'):
            explanations.append(f"Prix: {product['price']}€")
        
        return " - ".join(explanations)
    
    def _index_exists(self) -> bool:
        """Vérifie si l'index existe déjà"""
        manifest = IndexManifest.objects.filter(name='product_index').first()
        return manifest is not None and os.path.exists(manifest.file_path)
    
    def get_index_info(self) -> Dict[str, Any]:
        """Retourne des informations sur l'index"""
        manifest = IndexManifest.objects.filter(name='product_index').first()
        if not manifest:
            return {'exists': False}
        
        return {
            'exists': True,
            'version': manifest.version,
            'created_at': manifest.created_at.isoformat(),
            'product_count': manifest.metadata.get('product_count', 0),
            'file_path': manifest.file_path
        }


class RAGIndexManager:
    """Gestionnaire d'index pour le système RAG"""
    
    def __init__(self):
        self.document_processor = DocumentProcessor()
        self.retrieval_system = RAGRetrievalSystem()
        self.version_manager = IndexVersionManager()
        self.index_dir = getattr(settings, 'ML_INDEX_DIR', 'ml_indexes')
        os.makedirs(self.index_dir, exist_ok=True)
    
    def build_index(self, faq_data: List[Dict[str, Any]] = None,
                   policy_data: List[Dict[str, Any]] = None,
                   product_data: List[Dict[str, Any]] = None,
                   force_rebuild: bool = False) -> str:
        """Construit l'index RAG"""
        try:
            # Vérifier si l'index existe déjà
            if not force_rebuild and self._index_exists():
                logger.info("RAG index already exists, skipping build")
                return self.version_manager.get_current_version()
            
            logger.info("Building RAG index")
            
            # Vider le système existant
            self.retrieval_system.clear()
            
            # Traiter les documents FAQ
            if faq_data:
                faq_chunks = self.document_processor.process_faq_documents(faq_data)
                self.retrieval_system.add_documents(faq_chunks)
                logger.info(f"Added {len(faq_chunks)} FAQ chunks")
            
            # Traiter les documents de politique
            if policy_data:
                policy_chunks = self.document_processor.process_policy_documents(policy_data)
                self.retrieval_system.add_documents(policy_chunks)
                logger.info(f"Added {len(policy_chunks)} policy chunks")
            
            # Traiter les descriptions de produits
            if product_data:
                product_chunks = self.document_processor.process_product_descriptions(product_data)
                self.retrieval_system.add_documents(product_chunks)
                logger.info(f"Added {len(product_chunks)} product chunks")
            
            if not self.retrieval_system.chunks:
                raise ValueError("No documents to index")
            
            # Sauvegarder l'index
            index_path = os.path.join(self.index_dir, 'rag_index.pkl')
            self.retrieval_system.save(index_path)
            
            # Créer le manifest
            version = self.version_manager.increment_version()
            manifest = IndexManifest.objects.create(
                name='rag_index',
                version=version,
                file_path=index_path,
                metadata={
                    'chunk_count': len(self.retrieval_system.chunks),
                    'created_at': datetime.now().isoformat(),
                    'vectorizer_type': 'TF-IDF',
                    'faq_count': len([c for c in self.retrieval_system.chunks if c.metadata.get('type') == 'faq']),
                    'policy_count': len([c for c in self.retrieval_system.chunks if c.metadata.get('type') == 'policy']),
                    'product_count': len([c for c in self.retrieval_system.chunks if c.metadata.get('type') == 'product'])
                }
            )
            
            logger.info(f"RAG index built successfully: {version}")
            return version
            
        except Exception as e:
            logger.error(f"Error building RAG index: {e}")
            raise
    
    def load_index(self) -> bool:
        """Charge l'index RAG depuis le disque"""
        try:
            # Récupérer le manifest le plus récent
            manifest = IndexManifest.objects.filter(name='rag_index').first()
            if not manifest:
                logger.warning("No RAG index manifest found")
                return False
            
            # Charger l'index
            if os.path.exists(manifest.file_path):
                self.retrieval_system = RAGRetrievalSystem.load(manifest.file_path)
                logger.info(f"RAG index loaded: {manifest.version}")
                return True
            else:
                logger.error(f"RAG index file not found: {manifest.file_path}")
                return False
                
        except Exception as e:
            logger.error(f"Error loading RAG index: {e}")
            return False
    
    def ask_question(self, question: str, max_sources: int = 3) -> Dict[str, Any]:
        """Pose une question à l'assistant RAG"""
        if not self.retrieval_system.is_fitted:
            logger.warning("RAG index not ready")
            return {
                'answer': "L'assistant n'est pas encore prêt. Veuillez réessayer plus tard.",
                'sources': [],
                'confidence': 0.0,
                'trace_id': None
            }
        
        try:
            from .rag.retrieval_system import RAGAssistant
            assistant = RAGAssistant(self.retrieval_system)
            return assistant.ask(question, max_sources)
        except Exception as e:
            logger.error(f"Error asking question: {e}")
            return {
                'answer': "Une erreur est survenue lors du traitement de votre question.",
                'sources': [],
                'confidence': 0.0,
                'trace_id': None
            }
    
    def _index_exists(self) -> bool:
        """Vérifie si l'index RAG existe déjà"""
        manifest = IndexManifest.objects.filter(name='rag_index').first()
        return manifest is not None and os.path.exists(manifest.file_path)
    
    def get_index_info(self) -> Dict[str, Any]:
        """Retourne des informations sur l'index RAG"""
        manifest = IndexManifest.objects.filter(name='rag_index').first()
        if not manifest:
            return {'exists': False}
        
        return {
            'exists': True,
            'version': manifest.version,
            'created_at': manifest.created_at.isoformat(),
            'chunk_count': manifest.metadata.get('chunk_count', 0),
            'faq_count': manifest.metadata.get('faq_count', 0),
            'policy_count': manifest.metadata.get('policy_count', 0),
            'product_count': manifest.metadata.get('product_count', 0),
            'file_path': manifest.file_path
        }
