"""Point d'entrée de l'application FastAPI.

Assemble l'application, enregistre les routers et expose la documentation
OpenAPI auto-générée sur ``/docs``.
"""

from __future__ import annotations

import hashlib
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app import __version__
from app.config import get_settings
from app.db import init_db, run_migrations
from app.routers import health, projects, score

_STATIC_DIR = Path(__file__).parent / "static"


def _asset_version() -> str:
    """Calcule une empreinte de version des assets statiques (BIZ-104).

    Le hash agrège le contenu de ``app.js`` et ``style.css`` ; il change donc
    dès qu'un de ces fichiers est modifié, ce qui permet de « buster » le cache
    navigateur via une query string sur leurs URL.

    Returns:
        Une empreinte hexadécimale courte (12 caractères).
    """
    digest = hashlib.sha256()
    for name in ("app.js", "style.css"):
        path = _STATIC_DIR / name
        if path.exists():
            digest.update(path.read_bytes())
    return digest.hexdigest()[:12]


#: Empreinte des assets calculée une fois au démarrage (les fichiers sont
#: figés dans l'image conteneur, inutile de la recalculer à chaque requête).
_ASSET_VERSION = _asset_version()


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    """Initialise la base de données au démarrage de l'application.

    Sur SQLite (développement / tests), les tables sont créées directement
    depuis les modèles. Sur une base réelle (MySQL en production), le schéma
    est mis à niveau via les migrations Alembic versionnées (BIZ-29).

    Args:
        application: Instance FastAPI en cours de démarrage.

    Yields:
        Le contrôle pendant la durée de vie de l'application.
    """
    if get_settings().database_url.startswith("sqlite"):
        init_db()
    else:
        run_migrations()
    yield


def create_app() -> FastAPI:
    """Construit et configure l'instance FastAPI.

    Returns:
        L'application FastAPI prête à être servie.
    """
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        version=__version__,
        description=(
            "API de création automatisée de Business Plans et de scoring de "
            "pertinence de projets internes."
        ),
        lifespan=lifespan,
    )
    application.include_router(health.router)
    application.include_router(score.router)
    application.include_router(projects.router)

    application.mount(
        "/static",
        StaticFiles(directory=_STATIC_DIR),
        name="static",
    )

    @application.get("/", include_in_schema=False)
    def index() -> HTMLResponse:
        """Sert l'interface web (single-page application).

        Le HTML est servi en ``no-cache`` et les références aux assets
        (``app.js`` / ``style.css``) sont estampillées d'une empreinte de
        version (BIZ-104). Le navigateur revalide donc toujours la page et
        récupère immédiatement les assets dès qu'ils changent, sans servir de
        version obsolète depuis son cache.
        """
        html = (_STATIC_DIR / "index.html").read_text(encoding="utf-8")
        html = html.replace("__ASSET_VERSION__", _ASSET_VERSION)
        return HTMLResponse(html, headers={"Cache-Control": "no-cache"})

    return application


app = create_app()
