"""Client d'inférence IA agnostique au modèle (EPIC 3, BIZ-38).

Le client cible le contrat ``chat/completions`` exposé par Azure AI Foundry, qui
est commun à toutes les familles de modèles (Claude Sonnet, GPT, ...). Changer de
modèle ne requiert donc qu'une modification de configuration (déploiement,
endpoint) sans toucher au code.

Principe directeur (docs/architecture.md) : « l'IA rédige et raisonne, le backend
valide et calcule ». Ce module n'effectue aucun calcul métier ; il se contente de
transmettre un prompt et de restituer le texte produit, en traçant la
consommation de jetons. Le client est synchrone pour rester
cohérent avec le reste de l'application (sessions et routes synchrones).
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from typing import Protocol

import httpx

from app.config import Settings, get_settings
from app.services.ai.errors import AiConfigError, AiResponseError

logger = logging.getLogger("bizplan.ai")

# Scope OAuth des services cognitifs Azure (auth Entra ID / identité managée).
_COGNITIVE_SCOPE = "https://cognitiveservices.azure.com/.default"


class _AccessToken(Protocol):
    """Jeton d'accès minimal exposé par ``azure-identity``."""

    token: str


class _TokenCredential(Protocol):
    """Contrat minimal d'un credential ``azure-identity``."""

    def get_token(self, *scopes: str) -> _AccessToken:
        """Retourne un jeton d'accès pour les scopes demandés."""
        ...


@dataclass(frozen=True, slots=True)
class AiCompletion:
    """Résultat d'un appel au modèle.

    Attributes:
        text: Texte généré par le modèle.
        input_tokens: Nombre de jetons consommés en entrée (prompt).
        output_tokens: Nombre de jetons générés en sortie.
    """

    text: str
    input_tokens: int
    output_tokens: int


class AiClient(Protocol):
    """Contrat minimal d'un client IA, facilement substituable en test."""

    def complete(
        self,
        *,
        system: str,
        user: str,
        json_mode: bool = False,
        max_tokens: int | None = None,
    ) -> AiCompletion:
        """Produit une complétion à partir d'un prompt système et utilisateur.

        Args:
            system: Instruction système (rôle, contraintes, format attendu).
            user: Message utilisateur (données du projet, consignes).
            json_mode: Si vrai, demande au modèle une réponse JSON stricte.
            max_tokens: Plafond de jetons générés (défaut : configuration).

        Returns:
            La complétion générée et sa consommation de jetons.
        """
        ...


class FoundryClient:
    """Client ``chat/completions`` Azure AI Foundry basé sur ``httpx``.

    Attributes:
        settings: Configuration applicative (endpoint, déploiement, clé...).
    """

    def __init__(self, settings: Settings, *, transport: httpx.BaseTransport | None = None) -> None:
        """Initialise le client et valide la configuration requise.

        Args:
            settings: Configuration applicative.
            transport: Transport httpx optionnel (injecté en test).

        Raises:
            AiConfigError: Si l'endpoint, le déploiement ou le moyen
                d'authentification (clé API ou Entra ID) manquent.
        """
        if not settings.ai_endpoint or not settings.ai_deployment:
            raise AiConfigError(
                "Configuration IA incomplète : ai_endpoint et ai_deployment "
                "sont requis lorsque ai_enabled est actif."
            )
        if not settings.ai_api_key and not settings.ai_use_entra_id:
            raise AiConfigError(
                "Configuration IA incomplète : fournir ai_api_key ou activer "
                "ai_use_entra_id (authentification par identité managée)."
            )
        self.settings = settings
        self._transport = transport
        self._credential_lock = threading.Lock()
        self._credential: _TokenCredential | None = None

    @property
    def _url(self) -> str:
        """Construit l'URL d'inférence du déploiement configuré."""
        base = self.settings.ai_endpoint.rstrip("/")
        deployment = self.settings.ai_deployment
        version = self.settings.ai_api_version
        return f"{base}/openai/deployments/{deployment}/chat/completions?api-version={version}"

    def _auth_headers(self) -> dict[str, str]:
        """Construit l'en-tête d'authentification selon le mode configuré.

        Privilégie la clé API si elle est fournie (dev/test) ; sinon utilise un
        jeton Entra ID obtenu via l'identité managée (aucun secret stocké).

        Returns:
            Les en-têtes d'authentification à ajouter à la requête.

        Raises:
            AiConfigError: Si l'obtention du jeton Entra ID échoue.
        """
        if self.settings.ai_api_key:
            return {"api-key": self.settings.ai_api_key}
        return {"Authorization": f"Bearer {self._entra_token()}"}

    def _entra_token(self) -> str:
        """Obtient un jeton d'accès Entra ID pour les services cognitifs.

        Le credential ``azure-identity`` met les jetons en cache et les
        rafraîchit automatiquement ; il est créé une seule fois (paresseux).

        Returns:
            Le jeton d'accès OAuth.

        Raises:
            AiConfigError: Si ``azure-identity`` est absent ou si l'acquisition
                du jeton échoue.
        """
        if self._credential is None:
            with self._credential_lock:
                if self._credential is None:
                    try:
                        from azure.identity import DefaultAzureCredential
                    except ImportError as exc:  # pragma: no cover - dépendance prod
                        raise AiConfigError(
                            "azure-identity est requis pour l'authentification Entra ID."
                        ) from exc
                    self._credential = DefaultAzureCredential()
        try:
            return self._credential.get_token(_COGNITIVE_SCOPE).token
        except Exception as exc:  # pragma: no cover - dépend de l'environnement Azure
            raise AiConfigError(f"Échec d'obtention du jeton Entra ID : {exc}") from exc

    def complete(
        self,
        *,
        system: str,
        user: str,
        json_mode: bool = False,
        max_tokens: int | None = None,
    ) -> AiCompletion:
        """Appelle le modèle et restitue le texte généré.

        Args:
            system: Instruction système.
            user: Message utilisateur.
            json_mode: Demande une réponse JSON stricte si vrai.
            max_tokens: Plafond de jetons générés (défaut : configuration).

        Returns:
            La complétion générée et sa consommation de jetons.

        Raises:
            AiResponseError: Si la réponse HTTP est en erreur ou si le contenu
                généré est absent.
        """
        token_limit = max_tokens or self.settings.ai_max_tokens
        token_param = (
            "max_completion_tokens" if self.settings.ai_use_max_completion_tokens else "max_tokens"
        )
        payload: dict[str, object] = {
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            token_param: token_limit,
            "temperature": 0.4,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        headers = {"Content-Type": "application/json", **self._auth_headers()}

        try:
            with httpx.Client(
                timeout=self.settings.ai_timeout_s, transport=self._transport
            ) as client:
                response = client.post(self._url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError as exc:
            raise AiResponseError(f"Échec de l'appel au modèle IA : {exc}") from exc

        try:
            text = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            input_tokens = int(usage.get("prompt_tokens", 0))
            output_tokens = int(usage.get("completion_tokens", 0))
        except (KeyError, IndexError, TypeError) as exc:
            raise AiResponseError("Réponse du modèle IA inexploitable.") from exc

        if not text:
            raise AiResponseError("Le modèle IA a renvoyé un contenu vide.")

        # Traçabilité du coût : ne jamais logguer le contenu.
        logger.info(
            "Appel IA déploiement=%s input_tokens=%d output_tokens=%d",
            self.settings.ai_deployment,
            input_tokens,
            output_tokens,
        )
        return AiCompletion(
            text=text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )


def get_ai_client(settings: Settings | None = None) -> AiClient:
    """Fabrique le client IA à partir de la configuration.

    Args:
        settings: Configuration applicative (défaut : configuration partagée).

    Returns:
        Un client IA prêt à l'emploi.

    Raises:
        AiConfigError: Si la configuration IA est incomplète.
    """
    resolved = settings or get_settings()
    return FoundryClient(resolved)
