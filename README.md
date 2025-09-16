# SmartMarket — TP-02 (API DRF, RGPD, Sécurité)

## Prérequis
- Python 3.10+
- Linux/macOS/WSL

## Installation rapide (Docker)
```bash
cp .env.example .env
make up          # build + démarre le service web
make migrate     # applique les migrations
make seed        # remplit des données de démo
```

Accès :
- Application : http://localhost:8000/
- Admin : http://localhost:8000/admin (créez un compte admin : `make superuser`)
- API DRF : http://localhost:8000/api/v1/
- Documentation OpenAPI :
  - Swagger : http://localhost:8000/api/v1/docs/
  - Redoc : http://localhost:8000/api/v1/redoc/

Commandes utiles :
```bash
make test        # lance pytest
make lint        # ruff + black --check
make fmt         # ruff --fix + black
make logs        # logs du service web
make down        # stoppe les services
```

## Installation locale (option)
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install --upgrade pip -r requirements.txt
cp .env.example .env
python manage.py migrate && python manage.py runserver
```

## API REST (DRF)
- Endpoints versionnés : `/api/v1/`
- **categories** : liste/détail (lecture publique)
- **products** : liste/détail (lecture publique), création/édition/suppression réservées (admin/manager)
- **orders** : création/lecture authentifiées ; chaque utilisateur ne consulte que ses propres commandes ; admin/manager voient tout
- **RGPD** :
  - Export : `GET /api/v1/rgpd/export/` (profil + commandes)
  - Suppression : `POST /api/v1/rgpd/erase/` (désactivation + anonymisation commandes)

### Authentification & rôles
- Session Django (CSRF actif)
- Groupes : `admin`, `manager`, `client`
- Permissions DRF :
  - `client` : lecture catalogue, gestion de ses commandes
  - `manager/admin` : gestion CRUD du catalogue, supervision commandes

### Sécurité
- CSRF, CORS whitelist dev, en-têtes `SECURE_*` en prod
- Throttling :
  - Public : 60 req/min
  - Authentifié : 120 req/min
  - Endpoints sensibles (login, reset, export, erase) : 10 req/min
- Mots de passe : Argon2, longueur ≥ 12, validateurs natifs
- Journalisation RGPD : logs internes (qui, quand, quoi)

### RGPD
- Export JSON des données utilisateur (profil + commandes)
- Suppression logique : désactivation + anonymisation commandes
- Journalisation de l’opération (logs)

## Exemples d’appels API
```bash
# Liste des produits (public)
curl http://localhost:8000/api/v1/products/

# Création d’une commande (authentifié)
curl -X POST -b cookies.txt -c cookies.txt \
  -d 'product_id=1&quantity=2' http://localhost:8000/api/v1/orders/

# Export RGPD (authentifié)
curl -b cookies.txt http://localhost:8000/api/v1/rgpd/export/

# Suppression RGPD (authentifié)
curl -X POST -b cookies.txt http://localhost:8000/api/v1/rgpd/erase/
```

## Tests
```bash
pytest --cov=catalog --cov=accounts
```
- Couverture cible : ≥ 60% (actuelle : >90%)
- Scénarios testés : authentification, permissions, throttling, RGPD, erreurs 400/403/404

## Variables d’environnement (.env)
Voir `.env.example` fourni. Par défaut, la base est SQLite (`db.sqlite3`).

## Rôles de test
- **admin** : gestion totale (catalogue, commandes)
- **manager** : gestion catalogue, supervision commandes
- **client** : lecture catalogue, gestion de ses commandes

## Qualité & audit
- Lint : `black`, `ruff`
- Tests : `pytest`, `pytest-cov`
- Audit dépendances : `pip-audit`

## Sécurité (résumé)
- Hash mots de passe : Argon2 (fallback PBKDF2)
- CSRF, CORS, en-têtes sécurité, cookies sécurisés
- Throttling global/utilisateur/sensible
- Journalisation RGPD

## Livrables
- Code source, configuration DRF, schéma OpenAPI, README
- Fichiers de config qualité/tests (black, ruff, pytest, coverage)
- (Captures à faire : UI Swagger/Redoc, export RGPD, refus d’accès)
- (Optionnel : scripts curl ou collection Postman)

