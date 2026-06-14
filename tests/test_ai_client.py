"""Tests du client d'inférence IA (BIZ-38).

Aucun appel réseau réel : les réponses HTTP sont simulées via
``httpx.MockTransport``.
"""

from __future__ import annotations

import httpx
import pytest

from app.config import Settings
from app.services.ai.client import FoundryClient
from app.services.ai.errors import AiConfigError, AiResponseError


def _settings() -> Settings:
    """Construit une configuration IA complète pour les tests."""
    return Settings(
        ai_enabled=True,
        ai_endpoint="https://exemple.cognitiveservices.azure.com",
        ai_deployment="mon-modele",
        ai_api_version="2024-10-21",
        ai_api_key="cle-de-test",
    )


def test_client_config_incomplete_leve_erreur() -> None:
    settings = Settings(ai_enabled=True, ai_endpoint="", ai_deployment="", ai_api_key="")
    with pytest.raises(AiConfigError):
        FoundryClient(settings)


def test_url_inclut_deployment_et_version() -> None:
    client = FoundryClient(_settings())
    assert "deployments/mon-modele" in client._url
    assert "api-version=2024-10-21" in client._url


def test_complete_retourne_texte_et_tokens() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "Texte généré."}}],
                "usage": {"prompt_tokens": 12, "completion_tokens": 34},
            },
        )

    client = FoundryClient(_settings(), transport=httpx.MockTransport(handler))
    result = client.complete(system="sys", user="usr")
    assert result.text == "Texte généré."
    assert result.input_tokens == 12
    assert result.output_tokens == 34


def test_complete_erreur_http_leve_ai_response_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": "boom"})

    client = FoundryClient(_settings(), transport=httpx.MockTransport(handler))
    with pytest.raises(AiResponseError):
        client.complete(system="sys", user="usr")


def test_complete_contenu_vide_leve_ai_response_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"choices": [{"message": {"content": ""}}]})

    client = FoundryClient(_settings(), transport=httpx.MockTransport(handler))
    with pytest.raises(AiResponseError):
        client.complete(system="sys", user="usr")


def test_complete_json_mode_ajoute_response_format() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        import json

        captured.update(json.loads(request.content))
        return httpx.Response(200, json={"choices": [{"message": {"content": "{}"}}], "usage": {}})

    client = FoundryClient(_settings(), transport=httpx.MockTransport(handler))
    client.complete(system="sys", user="usr", json_mode=True)
    assert captured["response_format"] == {"type": "json_object"}
