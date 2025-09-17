from django.urls import path
from . import views

app_name = 'ml'

urlpatterns = [
    # Recommandations
    path('products/<int:product_id>/recommendations/', 
         views.product_recommendations, 
         name='product_recommendations'),
    
    # Recherche sémantique
    path('search/', 
         views.semantic_search, 
         name='semantic_search'),
    
    # Assistant RAG
    path('assistant/ask/', 
         views.assistant_ask, 
         name='assistant_ask'),
    
    # Administration des index
    path('index/status/', 
         views.index_status, 
         name='index_status'),
    
    path('index/rebuild/', 
         views.rebuild_indexes, 
         name='rebuild_indexes'),
    
    # Logs et monitoring
    path('logs/search/', 
         views.search_logs, 
         name='search_logs'),
]
