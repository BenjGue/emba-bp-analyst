#!/bin/sh
# Point d'entrée du conteneur (BIZ-29).
#
# Applique les migrations de schéma versionnées (Alembic) AVANT de démarrer le
# serveur applicatif. La migration est exécutée une seule fois, ici, plutôt que
# dans chaque worker uvicorn, ce qui évite toute course concurrente sur le DDL.
set -e

# La base peut être brièvement injoignable (cold start, serveur MySQL en cours
# de démarrage après un réveil keep-awake). Plutôt que de crasher immédiatement
# (set -e), on retente la migration avec un backoff borné : le conteneur attend
# que la base redevienne disponible puis démarre proprement (BIZ-84).
MAX_ATTEMPTS="${DB_MIGRATION_MAX_ATTEMPTS:-30}"
RETRY_DELAY="${DB_MIGRATION_RETRY_DELAY:-5}"

echo "▶ Application des migrations de base de données (alembic upgrade head)..."
attempt=1
until alembic upgrade head; do
  if [ "$attempt" -ge "$MAX_ATTEMPTS" ]; then
    echo "❌ Échec des migrations après ${attempt} tentatives — abandon."
    exit 1
  fi
  echo "⏳ Base indisponible (tentative ${attempt}/${MAX_ATTEMPTS}) — nouvel essai dans ${RETRY_DELAY}s…"
  attempt=$((attempt + 1))
  sleep "$RETRY_DELAY"
done

echo "▶ Démarrage de l'API (uvicorn)..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
