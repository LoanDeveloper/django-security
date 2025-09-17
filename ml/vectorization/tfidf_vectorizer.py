import pickle
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Any, Tuple
import os
from django.conf import settings


class TFIDFVectorizer:
    """Vectoriseur TF-IDF pour les recommandations basées contenu"""
    
    def __init__(self, max_features=1000, min_df=2, max_df=0.8):
        self.vectorizer = TfidfVectorizer(
            max_features=max_features,
            min_df=min_df,
            max_df=max_df,
            ngram_range=(1, 2),
            stop_words=None  # On utilise notre propre preprocessing
        )
        self.feature_names = None
        self.is_fitted = False
        
    def fit(self, texts: List[str]) -> 'TFIDFVectorizer':
        """Entraîne le vectoriseur sur les textes"""
        self.vectorizer.fit(texts)
        self.feature_names = self.vectorizer.get_feature_names_out()
        self.is_fitted = True
        return self
    
    def transform(self, texts: List[str]) -> np.ndarray:
        """Transforme les textes en vecteurs TF-IDF"""
        if not self.is_fitted:
            raise ValueError("Vectorizer must be fitted before transform")
        return self.vectorizer.transform(texts).toarray()
    
    def fit_transform(self, texts: List[str]) -> np.ndarray:
        """Entraîne et transforme en une seule opération"""
        return self.fit(texts).transform(texts)
    
    def compute_similarity(self, query_vector: np.ndarray, 
                          document_vectors: np.ndarray) -> np.ndarray:
        """Calcule la similarité cosinus entre un vecteur requête et des vecteurs documents"""
        return cosine_similarity(query_vector.reshape(1, -1), document_vectors)[0]
    
    def get_feature_importance(self, vector: np.ndarray, top_k: int = 10) -> List[Tuple[str, float]]:
        """Retourne les features les plus importantes pour un vecteur"""
        if self.feature_names is None:
            return []
        
        # Obtenir les indices des valeurs les plus importantes
        top_indices = np.argsort(vector)[-top_k:][::-1]
        
        return [
            (self.feature_names[idx], vector[idx]) 
            for idx in top_indices 
            if vector[idx] > 0
        ]
    
    def save(self, filepath: str) -> None:
        """Sauvegarde le vectoriseur"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'wb') as f:
            pickle.dump({
                'vectorizer': self.vectorizer,
                'feature_names': self.feature_names,
                'is_fitted': self.is_fitted
            }, f)
    
    @classmethod
    def load(cls, filepath: str) -> 'TFIDFVectorizer':
        """Charge un vectoriseur sauvegardé"""
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
        
        instance = cls()
        instance.vectorizer = data['vectorizer']
        instance.feature_names = data['feature_names']
        instance.is_fitted = data['is_fitted']
        
        return instance


class ProductVectorizer:
    """Vectoriseur spécialisé pour les produits"""
    
    def __init__(self, max_features=1000):
        self.tfidf = TFIDFVectorizer(max_features=max_features)
        self.product_ids = []
        self.product_vectors = None
        
    def fit_products(self, products: List[Dict[str, Any]]) -> 'ProductVectorizer':
        """Entraîne le vectoriseur sur une liste de produits"""
        texts = []
        self.product_ids = []
        
        for product in products:
            if product.get('is_active', True):  # Seulement les produits actifs
                processed_text = product.get('processed_text', '')
                if processed_text:
                    texts.append(processed_text)
                    self.product_ids.append(product['id'])
        
        if texts:
            self.product_vectors = self.tfidf.fit_transform(texts)
        
        return self
    
    def get_similar_products(self, product_id: int, top_k: int = 10, 
                           exclude_self: bool = True) -> List[Tuple[int, float]]:
        """Trouve les produits similaires à un produit donné"""
        if not self.is_ready():
            return []
        
        try:
            product_idx = self.product_ids.index(product_id)
        except ValueError:
            return []
        
        # Vecteur du produit de référence
        query_vector = self.product_vectors[product_idx]
        
        # Calculer les similarités
        similarities = self.tfidf.compute_similarity(query_vector, self.product_vectors)
        
        # Créer la liste des résultats avec indices
        results = [(self.product_ids[i], similarities[i]) for i in range(len(similarities))]
        
        # Exclure le produit lui-même si demandé
        if exclude_self:
            results = [(pid, score) for pid, score in results if pid != product_id]
        
        # Trier par similarité décroissante et retourner le top-k
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]
    
    def search_products(self, query_text: str, top_k: int = 10) -> List[Tuple[int, float]]:
        """Recherche des produits par similarité textuelle"""
        if not self.is_ready():
            return []
        
        # Vectoriser la requête
        query_vector = self.tfidf.transform([query_text])
        
        # Calculer les similarités
        similarities = self.tfidf.compute_similarity(query_vector[0], self.product_vectors)
        
        # Créer la liste des résultats
        results = [(self.product_ids[i], similarities[i]) for i in range(len(similarities))]
        
        # Trier par similarité décroissante et retourner le top-k
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]
    
    def get_explanation(self, product_id: int, similar_product_id: int) -> List[str]:
        """Génère une explication de la similarité entre deux produits"""
        if not self.is_ready():
            return []
        
        try:
            product_idx = self.product_ids.index(product_id)
            similar_idx = self.product_ids.index(similar_product_id)
        except ValueError:
            return []
        
        # Vecteurs des deux produits
        vector1 = self.product_vectors[product_idx]
        vector2 = self.product_vectors[similar_idx]
        
        # Features communes importantes
        common_features = []
        for i, (feature, score1) in enumerate(zip(self.tfidf.feature_names, vector1)):
            score2 = vector2[i]
            if score1 > 0 and score2 > 0:
                common_features.append((feature, min(score1, score2)))
        
        # Trier par importance et retourner les top features
        common_features.sort(key=lambda x: x[1], reverse=True)
        
        explanations = []
        for feature, score in common_features[:5]:
            if score > 0.1:  # Seuil minimum
                explanations.append(f"Caractéristique commune: {feature}")
        
        return explanations
    
    def is_ready(self) -> bool:
        """Vérifie si le vectoriseur est prêt à être utilisé"""
        return (self.tfidf.is_fitted and 
                self.product_vectors is not None and 
                len(self.product_ids) > 0)
    
    def save(self, filepath: str) -> None:
        """Sauvegarde le vectoriseur de produits"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'wb') as f:
            pickle.dump({
                'tfidf': self.tfidf,
                'product_ids': self.product_ids,
                'product_vectors': self.product_vectors
            }, f)
    
    @classmethod
    def load(cls, filepath: str) -> 'ProductVectorizer':
        """Charge un vectoriseur de produits sauvegardé"""
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
        
        instance = cls()
        instance.tfidf = data['tfidf']
        instance.product_ids = data['product_ids']
        instance.product_vectors = data['product_vectors']
        
        return instance
