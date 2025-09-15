# SmartMarket — TP-01 (socle Django: Catalog, Qualité)

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

Accès:
- Application: http://localhost:8000/
- Admin: http://localhost:8000/admin (créez un compte admin: `make superuser`)
- Debug Toolbar (dev): http://localhost:8000/__debug__/

Commandes utiles:
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

URLs:
- Racine: liste des produits
- Détail produit: /p/<slug>/
- Auth: /register, /login, /logout, /dashboard (protégée)

## Sécurité (résumé)
- Secrets via `.env` (django-environ)
- Hash mots de passe: Argon2 (fallback PBKDF2)
- Validateurs de mot de passe (longueur>=12, communs, numériques)
- CSRF activé, templates auto-escape
- Contrôle d’accès: `@login_required`
- Anti-brute force: django-axes (5 essais / 15 min, lockout 429)
- Cookies: Secure, HttpOnly, SameSite=Lax
- Headers: X-Frame-Options=DENY, Referrer-Policy strict-origin-when-cross-origin, HSTS (prod)
- Static via WhiteNoise
- Logs: `logs/auth.log` (rotation quotidienne) pour inscriptions, login, logout, lockout

## Tests
```bash
pytest -q
```

## Audit des dépendances
```bash
pip-audit
```

## Variables d’environnement (.env)
Voir `.env.example` fourni. Par défaut, la base est SQLite (`db.sqlite3`).

## Captures à fournir
- Admin → liste des produits avec filtres/actions visibles
- Debug toolbar avec requêtes sur la liste des produits
- Pages: liste des produits et détail

## Rapport sécurité (Markdown)

### Modèle CIA
- **Confidentialité**: sessions signées par `SECRET_KEY`, cookies `Secure`/`HttpOnly`/`SameSite`, CSRF activé, messages d’erreur génériques (anti-enumération).
- **Intégrité**: ORM Django (pas de SQL brut), validations de formulaires, Argon2 pour le hachage des mots de passe, en-têtes de sécurité.
- **Disponibilité**: throttling/lockout anti-brute force via `django-axes`.

### Mapping OWASP Top 10
- **A01 (Contrôle d’accès)**: `@login_required` pour `/dashboard`, pas de données sensibles exposées.
- **A02 (Cryptographie/mots de passe)**: Argon2 activé (+ PBKDF2 fallback), `AUTH_PASSWORD_VALIDATORS` (longueur ≥ 12, communs, numériques).
- **A03 (Injection/ORM/CSRF)**: ORM uniquement, protection CSRF sur tous les POST.
- **A05 (XSS/Headers)**: templates auto-échappés; `X_FRAME_OPTIONS='DENY'`, `SECURE_REFERRER_POLICY='strict-origin-when-cross-origin'`, `SECURE_SSL_REDIRECT` (prod), HSTS en prod.
- **A06 (Composants vulnérables)**: `requirements.txt` gelé; audit `pip-audit` OK au moment de la livraison.
- **A07 (Identification et Auth échouées)**: `django-axes` (5 essais/15 min), lockout avec réponse 429, périmètre IP + identifiant, messages génériques.
- **A09 (Logging & Monitoring)**: logs dédiés `logs/auth.log` (rotation quotidienne) pour inscriptions, logins, lockouts, logouts.

### Throttling / Lockout
- **Seuils**: 5 échecs en 15 minutes.
- **Périmètre**: IP + identifiant.
- **Durée**: cooloff 15 minutes (déverrouillage automatique après délai ou reset après succès si non verrouillé).

### Bonus (activables)
- **Confirmation d’email**: activée en dev (backend console), réglable via `REQUIRE_EMAIL_CONFIRM`.
- **2FA/CAPTCHA/Rate limiting global**: non inclus par défaut, intégrables si requis.

