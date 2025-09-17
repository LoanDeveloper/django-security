import time
import uuid
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.core.paginator import Paginator
from django.core.cache import cache
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.throttling import UserRateThrottle
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
import logging

from .index_manager import ProductIndexManager, RAGIndexManager
from .cache_manager import CacheManager, IndexVersionManager
from .models import SearchLog
from catalog.models import Product

logger = logging.getLogger(__name__)


class MLThrottle(UserRateThrottle):
    """Throttling spécifique pour les endpoints ML"""
    scope = 'ml_requests'


@api_view(['GET'])
def product_recommendations(request, product_id):
    """Endpoint pour les recommandations de produits"""
    start_time = time.time()
    
    try:
        # Paramètres
        k = int(request.GET.get('k', 10))
        k = min(k, 50)  # Limiter à 50 recommandations max
        
        # Gestionnaire de cache
        cache_manager = CacheManager()
        version_manager = IndexVersionManager()
        index_version = version_manager.get_current_version()
        
        # Vérifier le cache
        cached_result = cache_manager.get_recommendations(product_id, k, index_version)
        if cached_result:
            return Response({
                'product_id': product_id,
                'recommendations': cached_result,
                'count': len(cached_result),
                'cached': True,
                'index_version': index_version
            })
        
        # Charger l'index des produits
        product_manager = ProductIndexManager()
        if not product_manager.load_index():
            return Response({
                'error': 'Index des produits non disponible'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        # Récupérer les produits depuis la base de données
        products = {}
        for product in Product.objects.filter(is_active=True, stock__gt=0):
            products[product.id] = {
                'id': product.id,
                'name': product.name,
                'description': '',  # Pas de description dans le modèle
                'category': product.category.name if product.category else '',
                'price': float(product.price),
                'is_active': product.is_active,
                'stock_quantity': product.stock
            }
        
        # Obtenir les recommandations
        recommendations = product_manager.get_recommendations(product_id, k, products)
        
        # Mettre en cache
        cache_manager.set_recommendations(product_id, recommendations, k, index_version)
        
        # Calculer le temps de réponse
        response_time = int((time.time() - start_time) * 1000)
        
        return Response({
            'product_id': product_id,
            'recommendations': recommendations,
            'count': len(recommendations),
            'cached': False,
            'index_version': index_version,
            'response_time_ms': response_time
        })
        
    except Exception as e:
        logger.error(f"Error in product_recommendations: {e}")
        return Response({
            'error': 'Erreur lors de la récupération des recommandations'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def semantic_search(request):
    """Endpoint pour la recherche sémantique"""
    start_time = time.time()
    
    try:
        # Paramètres
        query = request.GET.get('q', '').strip()
        if not query:
            return Response({
                'error': 'Paramètre de requête "q" requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        k = int(request.GET.get('k', 20))
        k = min(k, 100)  # Limiter à 100 résultats max
        
        # Gestionnaire de cache
        cache_manager = CacheManager()
        version_manager = IndexVersionManager()
        index_version = version_manager.get_current_version()
        
        # Vérifier le cache
        cached_result = cache_manager.get_search_results(query, k, index_version)
        if cached_result:
            return Response({
                'query': query,
                'results': cached_result,
                'count': len(cached_result),
                'cached': True,
                'index_version': index_version
            })
        
        # Charger l'index des produits
        product_manager = ProductIndexManager()
        if not product_manager.load_index():
            return Response({
                'error': 'Index de recherche non disponible'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        # Récupérer les produits depuis la base de données
        products = {}
        for product in Product.objects.filter(is_active=True, stock__gt=0):
            products[product.id] = {
                'id': product.id,
                'name': product.name,
                'description': '',  # Pas de description dans le modèle
                'category': product.category.name if product.category else '',
                'price': float(product.price),
                'is_active': product.is_active,
                'stock_quantity': product.stock
            }
        
        # Effectuer la recherche
        results = product_manager.search_products(query, k, products)
        
        # Mettre en cache
        cache_manager.set_search_results(query, results, k, index_version)
        
        # Calculer le temps de réponse
        response_time = int((time.time() - start_time) * 1000)
        
        # Journaliser la recherche
        trace_id = str(uuid.uuid4())
        SearchLog.objects.create(
            trace_id=trace_id,
            query=query,
            results_count=len(results),
            top_k_scores=[r['similarity_score'] for r in results[:10]],
            index_version=index_version,
            response_time_ms=response_time
        )
        
        return Response({
            'query': query,
            'results': results,
            'count': len(results),
            'cached': False,
            'index_version': index_version,
            'response_time_ms': response_time,
            'trace_id': trace_id
        })
        
    except Exception as e:
        logger.error(f"Error in semantic_search: {e}")
        return Response({
            'error': 'Erreur lors de la recherche'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@throttle_classes([MLThrottle])
def assistant_ask(request):
    """Endpoint pour l'assistant RAG"""
    start_time = time.time()
    
    try:
        # Récupérer la question
        question = request.data.get('question', '').strip()
        if not question:
            return Response({
                'error': 'Question requise'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        max_sources = int(request.data.get('max_sources', 3))
        max_sources = min(max_sources, 10)  # Limiter à 10 sources max
        
        # Gestionnaire de cache
        cache_manager = CacheManager()
        version_manager = IndexVersionManager()
        index_version = version_manager.get_current_version()
        
        # Vérifier le cache
        cached_result = cache_manager.get_rag_response(question, max_sources, index_version)
        if cached_result:
            return Response({
                'question': question,
                'answer': cached_result['answer'],
                'sources': cached_result['sources'],
                'confidence': cached_result['confidence'],
                'trace_id': cached_result['trace_id'],
                'cached': True,
                'index_version': index_version
            })
        
        # Charger l'index RAG
        rag_manager = RAGIndexManager()
        if not rag_manager.load_index():
            return Response({
                'error': 'Assistant non disponible'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        # Poser la question
        response = rag_manager.ask_question(question, max_sources)
        
        # Mettre en cache
        cache_manager.set_rag_response(question, response, max_sources, index_version)
        
        # Calculer le temps de réponse
        response_time = int((time.time() - start_time) * 1000)
        
        # Journaliser la question
        trace_id = response.get('trace_id') or str(uuid.uuid4())
        SearchLog.objects.create(
            trace_id=trace_id,
            query=question,
            results_count=len(response.get('sources', [])),
            top_k_scores=[s.get('score', 0) for s in response.get('sources', [])],
            index_version=index_version,
            response_time_ms=response_time
        )
        
        return Response({
            'question': question,
            'answer': response['answer'],
            'sources': response['sources'],
            'confidence': response['confidence'],
            'trace_id': trace_id,
            'cached': False,
            'index_version': index_version,
            'response_time_ms': response_time
        })
        
    except Exception as e:
        logger.error(f"Error in assistant_ask: {e}")
        return Response({
            'error': 'Erreur lors du traitement de votre question'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def index_status(request):
    """Endpoint pour vérifier le statut des index"""
    try:
        product_manager = ProductIndexManager()
        rag_manager = RAGIndexManager()
        
        product_info = product_manager.get_index_info()
        rag_info = rag_manager.get_index_info()
        
        return Response({
            'product_index': product_info,
            'rag_index': rag_info,
            'cache_stats': CacheManager().get_cache_stats()
        })
        
    except Exception as e:
        logger.error(f"Error in index_status: {e}")
        return Response({
            'error': 'Erreur lors de la récupération du statut'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def rebuild_indexes(request):
    """Endpoint pour reconstruire les index"""
    try:
        # Récupérer les produits
        products = []
        for product in Product.objects.all():
            products.append({
                'id': product.id,
                'name': product.name,
                'description': '',  # Pas de description dans le modèle
                'category': product.category.name if product.category else '',
                'price': float(product.price),
                'is_active': product.is_active,
                'stock_quantity': product.stock
            })
        
        # Données FAQ (exemple)
        faq_data = [
            {
                'question': 'Comment passer une commande ?',
                'answer': 'Pour passer une commande, ajoutez les produits à votre panier et suivez le processus de checkout.',
                'category': 'commande'
            },
            {
                'question': 'Quels sont les modes de paiement acceptés ?',
                'answer': 'Nous acceptons les cartes bancaires, PayPal et les virements bancaires.',
                'category': 'paiement'
            },
            {
                'question': 'Quelle est la politique de retour ?',
                'answer': 'Vous pouvez retourner les produits dans les 30 jours suivant la livraison.',
                'category': 'retour'
            }
        ]
        
        # Données de politique (exemple)
        policy_data = [
            {
                'title': 'Politique de confidentialité',
                'content': 'Nous respectons votre vie privée et protégeons vos données personnelles conformément au RGPD.',
                'section': 'confidentialite',
                'category': 'legal'
            },
            {
                'title': 'Conditions générales de vente',
                'content': 'Les présentes conditions générales régissent l\'utilisation de notre site et les ventes.',
                'section': 'cgv',
                'category': 'legal'
            }
        ]
        
        # Reconstruire l'index des produits
        product_version = product_manager.build_index(products, force_rebuild=True)
        
        # Reconstruire l'index RAG
        rag_version = rag_manager.build_index(
            faq_data=faq_data,
            policy_data=policy_data,
            product_data=products,
            force_rebuild=True
        )
        
        # Invalider le cache
        cache_manager = CacheManager()
        cache_manager.invalidate_all_cache()
        
        return Response({
            'message': 'Index reconstruits avec succès',
            'product_index_version': product_version,
            'rag_index_version': rag_version
        })
        
    except Exception as e:
        logger.error(f"Error in rebuild_indexes: {e}")
        return Response({
            'error': 'Erreur lors de la reconstruction des index'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def search_logs(request):
    """Endpoint pour consulter les logs de recherche"""
    try:
        # Paramètres de pagination
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        page_size = min(page_size, 100)  # Limiter à 100 par page
        
        # Récupérer les logs
        logs = SearchLog.objects.all().order_by('-created_at')
        
        # Pagination
        paginator = Paginator(logs, page_size)
        page_obj = paginator.get_page(page)
        
        # Construire la réponse
        logs_data = []
        for log in page_obj:
            logs_data.append({
                'trace_id': str(log.trace_id),
                'query': log.query,
                'results_count': log.results_count,
                'top_k_scores': log.top_k_scores,
                'index_version': log.index_version,
                'response_time_ms': log.response_time_ms,
                'created_at': log.created_at.isoformat()
            })
        
        return Response({
            'logs': logs_data,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total_pages': paginator.num_pages,
                'total_count': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous()
            }
        })
        
    except Exception as e:
        logger.error(f"Error in search_logs: {e}")
        return Response({
            'error': 'Erreur lors de la récupération des logs'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
