# tracking-colis-cloudrun

Projet Flask de tracking colis (POC) prêt pour exécution locale et déploiement Google Cloud Run.

## Fonctionnalités

- Tracking public via `/track` et URL partageable `/track/<tracking_number>`.
- API JSON:
  - `GET /api/track/<tracking_number>`
  - `POST /api/track` (admin HTTP Basic)
  - `POST /api/events` (admin HTTP Basic)
  - `GET /api/status-codes`
  - `POST /api/webhook/status` (Bearer token)
- Back-office léger `/admin` (protégé HTTP Basic).
- Module legacy V1.0 préservé (auth/session + mini-ERP):
  - `/legacy` (ancienne homepage)
  - `/login`, `/register`, `/dashboard`, `/tracking`
  - `/facture` (génération PDF)
- Healthcheck `/healthz`.
- SQLite base unique (`instance/app.db`) avec seed de démonstration.

## Prérequis

- Python 3.12+
- Docker (optionnel)
- gcloud CLI (pour Cloud Run)

## Installation locale

```bash
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python init_db.py
make dev
```

Application locale: `http://localhost:8080`

- Page tracking: `http://localhost:8080/track/OSL-2026-0001`
- Admin: `http://localhost:8080/admin`

## Variables d'environnement

- `SECRET_KEY`
- `APP_ADMIN_USER`
- `APP_ADMIN_PASSWORD`
- `WEBHOOK_TOKEN`
- `DATABASE` (par défaut `instance/app.db`)

## Comptes legacy par défaut

- `admin` / `admin123`
- `test` / `test123`

## Initialiser la base

```bash
python init_db.py
```

Ce script crée les tables et un colis de démo `OSL-2026-0001` + événements.

## Docker local

```bash
make build
make docker-run
```

## Déploiement Cloud Run via Cloud Build

1. Créer Artifact Registry repo (une fois) :

```bash
gcloud artifacts repositories create cloud-run-images \
  --repository-format=docker --location=europe-west1
```

1. Lancer le build/déploiement :

```bash
gcloud builds submit --config cloudbuild.yaml .
```

Tu peux aussi surcharger les substitutions Cloud Build (`_REGION`, `_SERVICE`, `_REPO`, `_SECRET_KEY`, etc.).

## Exemples API

### GET tracking

```bash
curl http://localhost:8080/api/track/OSL-2026-0001
```

### POST création colis (admin)

```bash
curl -u admin:strong-password -X POST http://localhost:8080/api/track \
  -H "Content-Type: application/json" \
  -d '{
    "tracking_number":"OSL-2026-0099",
    "sender":"ACME",
    "recipient":"Madison",
    "origin":"TNR",
    "destination":"MRS",
    "service":"Express"
  }'
```

### POST événement

```bash
curl -u admin:strong-password -X POST http://localhost:8080/api/events \
  -H "Content-Type: application/json" \
  -d '{
    "tracking_number":"OSL-2026-0001",
    "code":"OUT_FOR_DELIVERY",
    "location":"Antananarivo",
    "ts":"2026-03-03T08:30:00Z",
    "details":"En cours de livraison"
  }'
```

### Webhook transporteur

```bash
curl -X POST http://localhost:8080/api/webhook/status \
  -H "Authorization: Bearer replace-with-strong-token" \
  -H "Content-Type: application/json" \
  -d '{
    "ref":"OSL-2026-0001",
    "status":"OUT_FOR_DELIVERY",
    "when":"2026-03-03T08:30:00Z",
    "city":"Antananarivo",
    "info":"En cours de livraison"
  }'
```

## Note production

Cloud Run est stateless: SQLite est acceptable pour une démo/POC, mais non recommandé en production.
Pour prod, migrer vers Cloud SQL PostgreSQL (et idéalement SQLAlchemy/Alembic pour les migrations).
