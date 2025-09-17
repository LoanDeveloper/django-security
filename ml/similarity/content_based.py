import numpy as np
from typing import List, Dict, Any, Tuple
from collections import Counter
import math


class ContentBasedRecommender:
    """Système de recommandation basé contenu avec diversité"""
    
    def __init__(self, diversity_weight: float = 0.3):
        self.diversity_weight = diversity_weight
        
    def compute_content_similarity(self, product1: Dict[str, Any], 
                                 product2: Dict[str, Any]) -> float:
        """Calcule la similarité entre deux produits basée sur leur contenu"""
        # Similarité textuelle (TF-IDF)
        text_sim = self._text_similarity(
            product1.get('processed_text', ''),
            product2.get('processed_text', '')
        )
        
        # Similarité catégorielle
        category_sim = self._category_similarity(
            product1.get('category', ''),
            product2.get('category', '')
        )
        
        # Similarité de prix (normalisée)
        price_sim = self._price_similarity(
            product1.get('price', 0),
            product2.get('price', 0)
        )
        
        # Pondération des similarités
        total_sim = (
            0.6 * text_sim +      # 60% similarité textuelle
            0.3 * category_sim +  # 30% similarité catégorielle
            0.1 * price_sim       # 10% similarité de prix
        )
        
        return total_sim
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """Calcule la similarité textuelle basée sur les mots communs"""
        if not text1 or not text2:
            return 0.0
        
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _category_similarity(self, cat1: str, cat2: str) -> float:
        """Calcule la similarité catégorielle"""
        if not cat1 or not cat2:
            return 0.0
        
        if cat1.lower() == cat2.lower():
            return 1.0
        
        # Similarité basée sur les mots communs dans les catégories
        words1 = set(cat1.lower().split())
        words2 = set(cat2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _price_similarity(self, price1: float, price2: float) -> float:
        """Calcule la similarité de prix (plus les prix sont proches, plus la similarité est élevée)"""
        if price1 == 0 and price2 == 0:
            return 1.0
        
        if price1 == 0 or price2 == 0:
            return 0.0
        
        # Utiliser la différence relative
        ratio = min(price1, price2) / max(price1, price2)
        return ratio
    
    def compute_diversity_score(self, recommendations: List[Tuple[int, float]], 
                              products: Dict[int, Dict[str, Any]]) -> float:
        """Calcule le score de diversité des recommandations"""
        if len(recommendations) <= 1:
            return 1.0
        
        # Extraire les catégories des produits recommandés
        categories = []
        for product_id, _ in recommendations:
            if product_id in products:
                category = products[product_id].get('category', '')
                if category:
                    categories.append(category)
        
        if not categories:
            return 0.0
        
        # Calculer l'entropie des catégories
        category_counts = Counter(categories)
        total = len(categories)
        
        entropy = 0.0
        for count in category_counts.values():
            p = count / total
            if p > 0:
                entropy -= p * math.log2(p)
        
        # Normaliser par l'entropie maximale possible
        max_entropy = math.log2(len(category_counts)) if len(category_counts) > 1 else 1.0
        diversity = entropy / max_entropy if max_entropy > 0 else 0.0
        
        return diversity
    
    def apply_diversity_filter(self, recommendations: List[Tuple[int, float]], 
                             products: Dict[int, Dict[str, Any]], 
                             target_diversity: float = 0.5) -> List[Tuple[int, float]]:
        """Applique un filtre de diversité aux recommandations"""
        if len(recommendations) <= 2:
            return recommendations
        
        # Algorithme de sélection diversifiée (simplifié)
        selected = []
        remaining = recommendations.copy()
        
        # Prendre le premier (le plus similaire)
        if remaining:
            selected.append(remaining.pop(0))
        
        # Sélectionner les suivants en maximisant la diversité
        while remaining and len(selected) < len(recommendations):
            best_candidate = None
            best_score = -1
            
            for i, (product_id, similarity) in enumerate(remaining):
                # Calculer le score combiné similarité + diversité
                temp_selected = selected + [(product_id, similarity)]
                diversity = self.compute_diversity_score(temp_selected, products)
                
                combined_score = (1 - self.diversity_weight) * similarity + \
                               self.diversity_weight * diversity
                
                if combined_score > best_score:
                    best_score = combined_score
                    best_candidate = i
            
            if best_candidate is not None:
                selected.append(remaining.pop(best_candidate))
            else:
                break
        
        return selected
    
    def filter_active_products(self, recommendations: List[Tuple[int, float]], 
                             products: Dict[int, Dict[str, Any]]) -> List[Tuple[int, float]]:
        """Filtre les recommandations pour ne garder que les produits actifs"""
        filtered = []
        for product_id, similarity in recommendations:
            if product_id in products:
                product = products[product_id]
                if product.get('is_active', True) and product.get('stock_quantity', 0) > 0:
                    filtered.append((product_id, similarity))
        
        return filtered
    
    def get_recommendation_explanations(self, product_id: int, 
                                      recommendations: List[Tuple[int, float]], 
                                      products: Dict[int, Dict[str, Any]]) -> Dict[int, List[str]]:
        """Génère des explications pour les recommandations"""
        explanations = {}
        
        if product_id not in products:
            return explanations
        
        source_product = products[product_id]
        
        for rec_product_id, similarity in recommendations:
            if rec_product_id not in products:
                continue
            
            rec_product = products[rec_product_id]
            explanation_parts = []
            
            # Explication basée sur la similarité textuelle
            text_sim = self._text_similarity(
                source_product.get('processed_text', ''),
                rec_product.get('processed_text', '')
            )
            
            if text_sim > 0.3:
                explanation_parts.append("Description similaire")
            
            # Explication basée sur la catégorie
            if source_product.get('category') == rec_product.get('category'):
                explanation_parts.append("Même catégorie")
            
            # Explication basée sur le prix
            price1 = source_product.get('price', 0)
            price2 = rec_product.get('price', 0)
            if price1 > 0 and price2 > 0:
                ratio = min(price1, price2) / max(price1, price2)
                if ratio > 0.8:
                    explanation_parts.append("Prix similaire")
                elif price2 < price1 * 0.7:
                    explanation_parts.append("Prix plus abordable")
                elif price2 > price1 * 1.3:
                    explanation_parts.append("Prix plus élevé")
            
            # Explication basée sur les mots-clés communs
            keywords1 = set(source_product.get('keywords', []))
            keywords2 = set(rec_product.get('keywords', []))
            common_keywords = keywords1.intersection(keywords2)
            
            if common_keywords:
                explanation_parts.append(f"Mots-clés communs: {', '.join(list(common_keywords)[:3])}")
            
            explanations[rec_product_id] = explanation_parts if explanation_parts else ["Produit similaire"]
        
        return explanations
