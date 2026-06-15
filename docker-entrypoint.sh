#!/bin/sh
# Point d'entrée du conteneur (BIZ-29).
#
# Applique les migrations de schéma versionnées (Alembic) AVANT de démarrer le
# serveur applicatif. La migration est exécutée une seule fois, ici, plutôt que
# dans chaque worker uvicorn, ce qui évite toute course concurrente sur le DDL.
set -e

echo "▶ Application des migrations de base de données (alembic upgrade head)..."
alembic upgrade head

echo "▶ Démarrage de l'API (uvicorn)..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
