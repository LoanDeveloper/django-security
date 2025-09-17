from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
import logging

from catalog.models import Product
from .cache_manager import CacheManager

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Product)
def invalidate_cache_on_product_save(sender, instance, **kwargs):
    """Invalide le cache ML quand un produit est sauvegardé"""
    try:
        cache_manager = CacheManager()
        cache_manager.invalidate_product_cache(instance.id)
        logger.info(f"Cache invalidated for product {instance.id} (save)")
    except Exception as e:
        logger.error(f"Error invalidating cache on product save: {e}")


@receiver(post_delete, sender=Product)
def invalidate_cache_on_product_delete(sender, instance, **kwargs):
    """Invalide le cache ML quand un produit est supprimé"""
    try:
        cache_manager = CacheManager()
        cache_manager.invalidate_product_cache(instance.id)
        logger.info(f"Cache invalidated for product {instance.id} (delete)")
    except Exception as e:
        logger.error(f"Error invalidating cache on product delete: {e}")
