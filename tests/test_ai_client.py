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


def test_complete_utilise_max_completion_tokens_par_defaut() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        import json

        captured.update(json.loads(request.content))
        return httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}], "usage": {}})

    client = FoundryClient(_settings(), transport=httpx.MockTransport(handler))
    client.complete(system="sys", user="usr")
    assert "max_completion_tokens" in captured
    assert "max_tokens" not in captured


def test_complete_param_legacy_max_tokens() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        import json

        captured.update(json.loads(request.content))
        return httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}], "usage": {}})

    settings = Settings(
        ai_enabled=True,
        ai_endpoint="https://exemple.cognitiveservices.azure.com",
        ai_deployment="mon-modele",
        ai_api_key="cle-de-test",
        ai_use_max_completion_tokens=False,
    )
    client = FoundryClient(settings, transport=httpx.MockTransport(handler))
    client.complete(system="sys", user="usr")
    assert "max_tokens" in captured
    assert "max_completion_tokens" not in captured


def test_api_key_prioritaire_envoie_header_api_key() -> None:
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["api-key"] = request.headers.get("api-key", "")
        captured["authorization"] = request.headers.get("authorization", "")
        return httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}], "usage": {}})

    client = FoundryClient(_settings(), transport=httpx.MockTransport(handler))
    client.complete(system="sys", user="usr")
    assert captured["api-key"] == "cle-de-test"
    assert captured["authorization"] == ""


def test_entra_id_envoie_bearer_token() -> None:
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["authorization"] = request.headers.get("authorization", "")
        return httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}], "usage": {}})

    settings = Settings(
        ai_enabled=True,
        ai_endpoint="https://exemple.cognitiveservices.azure.com",
        ai_deployment="mon-modele",
        ai_api_key="",
        ai_use_entra_id=True,
    )
    client = FoundryClient(settings, transport=httpx.MockTransport(handler))
    # Évite tout appel réseau Azure : on injecte un faux credential.
    client._credential = _FakeCredential("jeton-test")
    client.complete(system="sys", user="usr")
    assert captured["authorization"] == "Bearer jeton-test"


def test_config_sans_cle_ni_entra_id_leve_erreur() -> None:
    settings = Settings(
        ai_enabled=True,
        ai_endpoint="https://exemple.cognitiveservices.azure.com",
        ai_deployment="mon-modele",
        ai_api_key="",
        ai_use_entra_id=False,
    )
    with pytest.raises(AiConfigError):
        FoundryClient(settings)


class _FakeToken:
    """Jeton factice exposant l'attribut ``token`` attendu par le client."""

    def __init__(self, value: str) -> None:
        self.token = value


class _FakeCredential:
    """Credential factice imitant ``DefaultAzureCredential.get_token``."""

    def __init__(self, value: str) -> None:
        self._value = value

    def get_token(self, *scopes: str) -> _FakeToken:
        return _FakeToken(self._value)
