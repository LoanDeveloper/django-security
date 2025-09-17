import json
import hashlib
from typing import Any, Dict, List, Optional
from django.core.cache import cache
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class CacheManager:
    """Gestionnaire de cache pour les recommandations et la recherche"""
    
    def __init__(self, default_timeout=3600):  # 1 heure par défaut
        self.default_timeout = default_timeout
        self.cache_prefix = "smartmarket_ml_"
        
    def _get_cache_key(self, key_type: str, **kwargs) -> str:
        """Génère une clé de cache unique"""
        # Créer un hash des paramètres pour la clé
        params_str = json.dumps(kwargs, sort_keys=True)
        params_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]
        
        return f"{self.cache_prefix}{key_type}_{params_hash}"
    
    def get_recommendations(self, product_id: int, k: int = 10, 
                          index_version: str = None) -> Optional[List[Dict[str, Any]]]:
        """Récupère les recommandations depuis le cache"""
        cache_key = self._get_cache_key(
            "recommendations", 
            product_id=product_id, 
            k=k, 
            index_version=index_version
        )
        
        try:
            result = cache.get(cache_key)
            if result:
                logger.info(f"Cache hit for recommendations: {cache_key}")
            return result
        except Exception as e:
            logger.error(f"Error getting recommendations from cache: {e}")
            return None
    
    def set_recommendations(self, product_id: int, recommendations: List[Dict[str, Any]], 
                          k: int = 10, index_version: str = None, 
                          timeout: int = None) -> bool:
        """Met en cache les recommandations"""
        cache_key = self._get_cache_key(
            "recommendations", 
            product_id=product_id, 
            k=k, 
            index_version=index_version
        )
        
        try:
            cache.set(cache_key, recommendations, timeout or self.default_timeout)
            logger.info(f"Cached recommendations: {cache_key}")
            return True
        except Exception as e:
            logger.error(f"Error caching recommendations: {e}")
            return False
    
    def get_search_results(self, query: str, k: int = 20, 
                         index_version: str = None) -> Optional[List[Dict[str, Any]]]:
        """Récupère les résultats de recherche depuis le cache"""
        cache_key = self._get_cache_key(
            "search", 
            query=query, 
            k=k, 
            index_version=index_version
        )
        
        try:
            result = cache.get(cache_key)
            if result:
                logger.info(f"Cache hit for search: {cache_key}")
            return result
        except Exception as e:
            logger.error(f"Error getting search results from cache: {e}")
            return None
    
    def set_search_results(self, query: str, results: List[Dict[str, Any]], 
                         k: int = 20, index_version: str = None, 
                         timeout: int = None) -> bool:
        """Met en cache les résultats de recherche"""
        cache_key = self._get_cache_key(
            "search", 
            query=query, 
            k=k, 
            index_version=index_version
        )
        
        try:
            cache.set(cache_key, results, timeout or self.default_timeout)
            logger.info(f"Cached search results: {cache_key}")
            return True
        except Exception as e:
            logger.error(f"Error caching search results: {e}")
            return False
    
    def get_rag_response(self, question: str, max_sources: int = 3, 
                        index_version: str = None) -> Optional[Dict[str, Any]]:
        """Récupère une réponse RAG depuis le cache"""
        cache_key = self._get_cache_key(
            "rag", 
            question=question, 
            max_sources=max_sources, 
            index_version=index_version
        )
        
        try:
            result = cache.get(cache_key)
            if result:
                logger.info(f"Cache hit for RAG: {cache_key}")
            return result
        except Exception as e:
            logger.error(f"Error getting RAG response from cache: {e}")
            return None
    
    def set_rag_response(self, question: str, response: Dict[str, Any], 
                        max_sources: int = 3, index_version: str = None, 
                        timeout: int = None) -> bool:
        """Met en cache une réponse RAG"""
        cache_key = self._get_cache_key(
            "rag", 
            question=question, 
            max_sources=max_sources, 
            index_version=index_version
        )
        
        try:
            cache.set(cache_key, response, timeout or self.default_timeout)
            logger.info(f"Cached RAG response: {cache_key}")
            return True
        except Exception as e:
            logger.error(f"Error caching RAG response: {e}")
            return False
    
    def invalidate_product_cache(self, product_id: int) -> None:
        """Invalide le cache pour un produit spécifique"""
        try:
            # Invalider les recommandations pour ce produit
            cache_key_pattern = f"{self.cache_prefix}recommendations_*product_id={product_id}*"
            self._invalidate_pattern(cache_key_pattern)
            
            # Invalider les recommandations qui incluent ce produit
            cache_key_pattern = f"{self.cache_prefix}recommendations_*"
            self._invalidate_pattern(cache_key_pattern)
            
            logger.info(f"Invalidated cache for product {product_id}")
        except Exception as e:
            logger.error(f"Error invalidating product cache: {e}")
    
    def invalidate_all_cache(self) -> None:
        """Invalide tout le cache ML"""
        try:
            cache_key_pattern = f"{self.cache_prefix}*"
            self._invalidate_pattern(cache_key_pattern)
            logger.info("Invalidated all ML cache")
        except Exception as e:
            logger.error(f"Error invalidating all cache: {e}")
    
    def _invalidate_pattern(self, pattern: str) -> None:
        """Invalide les clés de cache correspondant à un pattern"""
        # Note: Cette implémentation est simplifiée
        # Dans un environnement de production, vous devriez utiliser
        # un système de cache qui supporte les patterns (comme Redis)
        try:
            # Pour Django cache, on ne peut pas facilement invalider par pattern
            # On utilise une approche alternative avec des tags ou des versions
            cache.clear()
        except Exception as e:
            logger.error(f"Error invalidating pattern {pattern}: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Retourne des statistiques sur le cache"""
        try:
            # Cette implémentation dépend du backend de cache utilisé
            # Pour Redis, on pourrait utiliser des commandes spécifiques
            return {
                'backend': getattr(settings, 'CACHES', {}).get('default', {}).get('BACKEND', 'unknown'),
                'timeout': self.default_timeout,
                'prefix': self.cache_prefix
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {}


class IndexVersionManager:
    """Gestionnaire de versions d'index pour l'invalidation de cache"""
    
    def __init__(self):
        self.version_key = "smartmarket_index_version"
    
    def get_current_version(self) -> str:
        """Récupère la version actuelle de l'index"""
        try:
            version = cache.get(self.version_key)
            if not version:
                version = "1.0.0"
                self.set_version(version)
            return version
        except Exception as e:
            logger.error(f"Error getting index version: {e}")
            return "1.0.0"
    
    def set_version(self, version: str) -> None:
        """Définit la version de l'index"""
        try:
            cache.set(self.version_key, version, timeout=None)  # Pas d'expiration
            logger.info(f"Set index version to {version}")
        except Exception as e:
            logger.error(f"Error setting index version: {e}")
    
    def increment_version(self) -> str:
        """Incrémente la version de l'index"""
        try:
            current = self.get_current_version()
            # Version simple: incrémenter le dernier chiffre
            parts = current.split('.')
            if len(parts) >= 3:
                parts[-1] = str(int(parts[-1]) + 1)
                new_version = '.'.join(parts)
            else:
                new_version = f"{current}.1"
            
            self.set_version(new_version)
            return new_version
        except Exception as e:
            logger.error(f"Error incrementing version: {e}")
            return self.get_current_version()
    
    def invalidate_on_version_change(self) -> None:
        """Invalide le cache quand la version change"""
        try:
            # Incrémenter la version
            new_version = self.increment_version()
            
            # Invalider tout le cache ML
            cache_manager = CacheManager()
            cache_manager.invalidate_all_cache()
            
            logger.info(f"Invalidated cache due to version change to {new_version}")
        except Exception as e:
            logger.error(f"Error invalidating on version change: {e}")
