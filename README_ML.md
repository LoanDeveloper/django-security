# Module ML - SmartMarket

Ce module implémente les fonctionnalités de recommandations, recherche sémantique et assistant RAG pour SmartMarket.

## Prérequis

- Python 3.12+
- Django 4.2+
- scikit-learn 1.3.2+
- nltk 3.8.1+
- numpy 1.24.3+

## Installation

1. Installer les dépendances :
```bash
pip install -r requirements.txt
```

2. Appliquer les migrations :
```bash
python manage.py migrate
```

3. Construire les index ML :
```bash
python manage.py build_indexes
```

## Endpoints API

### Recommandations de produits
- **URL** : `/api/v1/products/{id}/recommendations/`
- **Méthode** : GET
- **Paramètres** :
  - `k` : nombre de recommandations (défaut: 10, max: 50)
- **Réponse** : Liste des produits recommandés avec scores de similarité et explications

### Recherche sémantique
- **URL** : `/api/v1/search/`
- **Méthode** : GET
- **Paramètres** :
  - `q` : requête de recherche (obligatoire)
  - `k` : nombre de résultats (défaut: 20, max: 100)
- **Réponse** : Liste des produits trouvés avec scores de similarité et raisons

### Assistant RAG
- **URL** : `/api/v1/assistant/ask/`
- **Méthode** : POST
- **Body** :
  ```json
  {
    "question": "Comment passer une commande ?",
    "max_sources": 3
  }
  ```
- **Réponse** : Réponse de l'assistant avec sources et niveau de confiance

### Administration des index
- **URL** : `/api/v1/index/status/`
- **Méthode** : GET
- **Réponse** : Statut des index et informations de version

- **URL** : `/api/v1/index/rebuild/`
- **Méthode** : POST
- **Réponse** : Reconstruction des index

### Logs de recherche
- **URL** : `/api/v1/logs/search/`
- **Méthode** : GET
- **Paramètres** :
  - `page` : numéro de page (défaut: 1)
  - `page_size` : taille de page (défaut: 20, max: 100)
- **Réponse** : Logs paginés des recherches effectuées

## Configuration

### Cache
Le module utilise le cache Django pour optimiser les performances :
- Cache des recommandations : 1 heure
- Cache des recherches : 1 heure
- Cache des réponses RAG : 1 heure

### Throttling
- Endpoints ML : 30 requêtes/minute par utilisateur
- Assistant RAG : throttling spécifique pour éviter la surcharge

### Index
Les index sont stockés dans le répertoire `ml_indexes/` :
- `product_index.pkl` : Index des produits pour recommandations
- `rag_index.pkl` : Index RAG pour l'assistant

## Commandes de gestion

### Construire les index
```bash
# Construire tous les index
python manage.py build_indexes

# Forcer la reconstruction
python manage.py build_indexes --force

# Construire seulement l'index des produits
python manage.py build_indexes --product-only

# Construire seulement l'index RAG
python manage.py build_indexes --rag-only
```

## Architecture

### Module de prétraitement
- `text_processor.py` : Nettoyage et normalisation du texte
- `product_preprocessor.py` : Préparation des données produits

### Module de vectorisation
- `tfidf_vectorizer.py` : Vectorisation TF-IDF pour similarité textuelle

### Module de similarité
- `content_based.py` : Recommandations basées contenu avec diversité

### Module RAG
- `document_processor.py` : Traitement des documents (FAQ, politiques, produits)
- `retrieval_system.py` : Système de récupération et assistant

### Gestion des index
- `index_manager.py` : Construction et gestion des index
- `cache_manager.py` : Gestion du cache et invalidation

## Tests

Exécuter les tests :
```bash
python manage.py test ml
```

## Limitations

- **Corpus de démonstration** : Le système utilise un petit corpus de données d'exemple
- **Performance** : Pour de gros volumes (>10k produits), considérer l'utilisation d'ANN (Approximate Nearest Neighbors)
- **Langue** : Optimisé pour le français, nécessite adaptation pour d'autres langues
- **Cache** : Utilise le cache local Django, Redis recommandé en production

## Budget de latence visé

- **Recommandations** : < 200ms (avec cache < 50ms)
- **Recherche sémantique** : < 300ms (avec cache < 100ms)
- **Assistant RAG** : < 500ms (avec cache < 200ms)

## Monitoring

Le module journalise :
- Temps de réponse des requêtes
- Nombre de résultats retournés
- Scores de similarité (top-K)
- Version des index utilisés
- Trace ID pour le suivi

Les logs sont accessibles via l'endpoint `/api/v1/logs/search/` et stockés en base de données.
