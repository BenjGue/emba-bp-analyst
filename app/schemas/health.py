"""Schémas Pydantic pour le healthcheck."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Réponse du endpoint de healthcheck.

    Attributes:
        status: État de l'application. Toujours ``"ok"`` lorsque l'API répond.
        app_name: Nom de l'application tel que défini en configuration.
        version: Version courante du backend.
    """

    status: Literal["ok"] = Field(default="ok", description="État de l'application.")
    app_name: str = Field(description="Nom de l'application.")
    version: str = Field(description="Version du backend.")
