"""Création automatique de tickets JIRA depuis les alertes GitHub Advanced Security.

Sur le modèle de l'automatisation E2E (BIZ-39, ``report-failures.js``), ce script
lit les alertes GHAS ouvertes du dépôt via l'API GitHub puis crée, pour chaque
nouvelle alerte non encore tracée, un ticket JIRA de type ``Tâche`` préfixé
« TECH — ». Le dédoublonnage repose sur un label unique par alerte
(``ghas-<categorie>-<numero>``) recherché dans JIRA avant toute création.

Sources couvertes :
    * Code scanning (CodeQL) — ``/code-scanning/alerts``
    * Secret scanning — ``/secret-scanning/alerts``
    * Dependabot — ``/dependabot/alerts``

Aucun secret n'est codé en dur : tout provient des variables d'environnement
(fournies par GitHub Secrets dans le workflow ``security-to-jira.yml``).

Variables attendues :
    * ``GITHUB_TOKEN``       jeton GitHub (``security-events: read``)
    * ``GITHUB_REPOSITORY``  dépôt ``owner/repo``
    * ``GITHUB_API_URL``     base API GitHub (défaut: ``https://api.github.com``)
    * ``JIRA_BASE_URL``      URL JIRA Cloud
    * ``JIRA_EMAIL``         e-mail du compte JIRA
    * ``JIRA_API_TOKEN``     jeton d'API Atlassian
    * ``JIRA_PROJECT_KEY``   clé projet (défaut: ``BIZ``)
    * ``JIRA_TASK_ISSUETYPE`` type d'issue (défaut: ``Tâche``)
    * ``RUN_URL``            URL du run GitHub Actions (audit)
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from typing import Any

import httpx

_GITHUB_API_VERSION = "2022-11-28"
_HTTP_TIMEOUT_S = 30.0
_PER_PAGE = 100


@dataclass(frozen=True)
class SecurityAlert:
    """Alerte de sécurité normalisée, indépendamment de sa source GHAS.

    Attributes:
        category: Famille d'alerte (``codescan``, ``secret`` ou ``dep``).
        number: Numéro d'alerte attribué par GitHub (unique par catégorie).
        severity: Sévérité lisible (ex. ``high``) ou ``inconnue``.
        summary: Titre court de l'alerte.
        details: Détails complémentaires (description, localisation).
        html_url: Lien vers l'alerte sur GitHub.
    """

    category: str
    number: int
    severity: str
    summary: str
    details: str
    html_url: str

    @property
    def dedup_label(self) -> str:
        """Label JIRA unique permettant le dédoublonnage de l'alerte."""
        return f"ghas-{self.category}-{self.number}"


@dataclass
class Report:
    """Synthèse d'une exécution du script.

    Attributes:
        created: Clés JIRA des tickets créés.
        skipped: Labels des alertes déjà tracées (ignorées).
        unavailable: Catégories non lisibles (fonctionnalité désactivée / droits).
    """

    created: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    unavailable: list[str] = field(default_factory=list)


def _require_env(name: str) -> str:
    """Retourne une variable d'environnement obligatoire ou lève une erreur.

    Args:
        name: Nom de la variable d'environnement.

    Returns:
        La valeur non vide de la variable.

    Raises:
        RuntimeError: Si la variable est absente ou vide.
    """
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Variable d'environnement requise manquante : {name}")
    return value


class FeatureUnavailableError(RuntimeError):
    """Catégorie d'alerte non lisible (désactivée ou droits insuffisants)."""


def _paginate(client: httpx.Client, path: str) -> list[dict[str, Any]]:
    """Récupère toutes les pages d'un endpoint d'alertes GitHub.

    Les codes 403/404 (fonctionnalité désactivée ou droits insuffisants) lèvent
    une ``FeatureUnavailableError`` pour que l'appelant ignore la catégorie.

    Args:
        client: Client HTTP configuré pour l'API GitHub.
        path: Chemin de l'endpoint (ex. ``/code-scanning/alerts``).

    Returns:
        La liste agrégée des objets d'alerte renvoyés par GitHub.

    Raises:
        FeatureUnavailableError: Si l'endpoint renvoie 403 ou 404.
    """
    results: list[dict[str, Any]] = []
    page = 1
    while True:
        response = client.get(
            path,
            params={"state": "open", "per_page": _PER_PAGE, "page": page},
        )
        if response.status_code in (403, 404):
            raise FeatureUnavailableError(f"{path} indisponible (HTTP {response.status_code})")
        response.raise_for_status()
        batch = response.json()
        if not isinstance(batch, list) or not batch:
            break
        results.extend(batch)
        if len(batch) < _PER_PAGE:
            break
        page += 1
    return results


def fetch_code_scanning_alerts(client: httpx.Client) -> list[SecurityAlert]:
    """Lit les alertes Code scanning ouvertes et les normalise."""
    alerts: list[SecurityAlert] = []
    for raw in _paginate(client, "/code-scanning/alerts"):
        rule = raw.get("rule") or {}
        severity = rule.get("security_severity_level") or rule.get("severity") or "inconnue"
        summary = rule.get("description") or rule.get("name") or "Alerte code scanning"
        message = (raw.get("most_recent_instance") or {}).get("message", {})
        alerts.append(
            SecurityAlert(
                category="codescan",
                number=int(raw["number"]),
                severity=str(severity),
                summary=str(summary),
                details=str(message.get("text", "")),
                html_url=str(raw.get("html_url", "")),
            )
        )
    return alerts


def fetch_secret_scanning_alerts(client: httpx.Client) -> list[SecurityAlert]:
    """Lit les alertes Secret scanning ouvertes et les normalise."""
    alerts: list[SecurityAlert] = []
    for raw in _paginate(client, "/secret-scanning/alerts"):
        secret_type = str(raw.get("secret_type_display_name") or raw.get("secret_type") or "secret")
        alerts.append(
            SecurityAlert(
                category="secret",
                number=int(raw["number"]),
                severity="critical",
                summary=f"Secret exposé : {secret_type}",
                details=f"Type: {secret_type}. Révoquez et faites tourner ce secret immédiatement.",
                html_url=str(raw.get("html_url", "")),
            )
        )
    return alerts


def fetch_dependabot_alerts(client: httpx.Client) -> list[SecurityAlert]:
    """Lit les alertes Dependabot ouvertes et les normalise."""
    alerts: list[SecurityAlert] = []
    for raw in _paginate(client, "/dependabot/alerts"):
        advisory = raw.get("security_advisory") or {}
        dependency = (raw.get("dependency") or {}).get("package") or {}
        package = str(dependency.get("name") or "dépendance")
        alerts.append(
            SecurityAlert(
                category="dep",
                number=int(raw["number"]),
                severity=str(advisory.get("severity") or "inconnue"),
                summary=f"Dépendance vulnérable : {package}",
                details=str(advisory.get("summary") or "Voir l'avis de sécurité lié."),
                html_url=str(raw.get("html_url", "")),
            )
        )
    return alerts


def _adf_paragraph(text: str) -> dict[str, Any]:
    """Construit un paragraphe ADF à partir d'un texte simple."""
    return {"type": "paragraph", "content": [{"type": "text", "text": text}]}


def build_description(alert: SecurityAlert, run_url: str) -> dict[str, Any]:
    """Construit la description ADF d'un ticket à partir d'une alerte.

    Args:
        alert: Alerte de sécurité normalisée.
        run_url: URL du run GitHub Actions pour audit.

    Returns:
        Un document ADF prêt à être envoyé à l'API JIRA.
    """
    content: list[dict[str, Any]] = [
        _adf_paragraph(f"Source : GitHub Advanced Security ({alert.category})."),
        _adf_paragraph(f"Sévérité : {alert.severity}."),
        _adf_paragraph(alert.summary),
    ]
    if alert.details:
        content.append(_adf_paragraph(alert.details))
    if alert.html_url:
        content.append(_adf_paragraph(f"Alerte GitHub : {alert.html_url}"))
    content.append(_adf_paragraph(f"Run CI : {run_url}"))
    return {"type": "doc", "version": 1, "content": content}


def jira_issue_exists(client: httpx.Client, project_key: str, label: str) -> bool:
    """Indique si un ticket portant ce label existe déjà dans le projet.

    Args:
        client: Client HTTP configuré pour l'API JIRA.
        project_key: Clé du projet JIRA (ex. ``BIZ``).
        label: Label unique de dédoublonnage de l'alerte.

    Returns:
        ``True`` si au moins un ticket correspond, ``False`` sinon.
    """
    jql = f'project = "{project_key}" AND labels = "{label}"'
    response = client.post(
        "/rest/api/3/search/jql",
        json={"jql": jql, "maxResults": 1, "fields": ["key"]},
    )
    response.raise_for_status()
    issues = response.json().get("issues") or []
    return len(issues) > 0


def create_jira_issue(
    client: httpx.Client,
    project_key: str,
    issuetype: str,
    alert: SecurityAlert,
    run_url: str,
) -> str:
    """Crée un ticket JIRA pour une alerte et renvoie sa clé.

    Args:
        client: Client HTTP configuré pour l'API JIRA.
        project_key: Clé du projet JIRA.
        issuetype: Nom du type d'issue (ex. ``Tâche``).
        alert: Alerte de sécurité à tracer.
        run_url: URL du run GitHub Actions pour audit.

    Returns:
        La clé du ticket créé (ex. ``BIZ-123``).
    """
    fields: dict[str, Any] = {
        "project": {"key": project_key},
        "summary": f"TECH — Sécurité : {alert.summary} ({alert.dedup_label})",
        "issuetype": {"name": issuetype},
        "labels": ["ghas", f"ghas-{alert.category}", alert.dedup_label],
        "description": build_description(alert, run_url),
    }
    response = client.post("/rest/api/3/issue", json={"fields": fields})
    response.raise_for_status()
    return str(response.json()["key"])


def collect_alerts(github: httpx.Client, report: Report) -> list[SecurityAlert]:
    """Agrège les alertes des trois sources GHAS en gérant les indisponibilités.

    Args:
        github: Client HTTP configuré pour l'API GitHub.
        report: Synthèse mise à jour avec les catégories indisponibles.

    Returns:
        La liste de toutes les alertes lisibles.
    """
    alerts: list[SecurityAlert] = []
    fetchers = {
        "code-scanning": fetch_code_scanning_alerts,
        "secret-scanning": fetch_secret_scanning_alerts,
        "dependabot": fetch_dependabot_alerts,
    }
    for name, fetcher in fetchers.items():
        try:
            alerts.extend(fetcher(github))
        except FeatureUnavailableError as exc:
            report.unavailable.append(name)
            print(f"[ignoré] {name} : {exc}")
    return alerts


def run(
    github: httpx.Client,
    jira: httpx.Client,
    project_key: str,
    issuetype: str,
    run_url: str,
) -> Report:
    """Exécute le flux complet : lecture des alertes puis création des tickets.

    Args:
        github: Client HTTP configuré pour l'API GitHub.
        jira: Client HTTP configuré pour l'API JIRA.
        project_key: Clé du projet JIRA.
        issuetype: Nom du type d'issue JIRA.
        run_url: URL du run GitHub Actions pour audit.

    Returns:
        La synthèse de l'exécution (créés, ignorés, indisponibles).
    """
    report = Report()
    for alert in collect_alerts(github, report):
        if jira_issue_exists(jira, project_key, alert.dedup_label):
            report.skipped.append(alert.dedup_label)
            continue
        key = create_jira_issue(jira, project_key, issuetype, alert, run_url)
        report.created.append(key)
        print(f"Ticket créé : {key} ({alert.dedup_label})")
    return report


def _build_github_client(token: str, repository: str, api_url: str) -> httpx.Client:
    """Construit le client HTTP pour l'API GitHub."""
    return httpx.Client(
        base_url=f"{api_url.rstrip('/')}/repos/{repository}",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": _GITHUB_API_VERSION,
        },
        timeout=_HTTP_TIMEOUT_S,
    )


def _build_jira_client(base_url: str, email: str, token: str) -> httpx.Client:
    """Construit le client HTTP pour l'API JIRA Cloud."""
    return httpx.Client(
        base_url=base_url.rstrip("/"),
        auth=(email, token),
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        timeout=_HTTP_TIMEOUT_S,
    )


def main() -> int:
    """Point d'entrée CLI. Lit l'environnement et lance le flux GHAS → JIRA.

    Returns:
        Code de sortie processus (toujours 0 : automatisation best-effort).
    """
    try:
        github_token = _require_env("GITHUB_TOKEN")
        repository = _require_env("GITHUB_REPOSITORY")
        jira_base_url = _require_env("JIRA_BASE_URL")
        jira_email = _require_env("JIRA_EMAIL")
        jira_token = _require_env("JIRA_API_TOKEN")
    except RuntimeError as exc:
        print(f"Configuration incomplète, abandon sans erreur : {exc}")
        return 0

    api_url = os.environ.get("GITHUB_API_URL", "https://api.github.com")
    project_key = os.environ.get("JIRA_PROJECT_KEY", "BIZ")
    issuetype = os.environ.get("JIRA_TASK_ISSUETYPE", "Tâche")
    run_url = os.environ.get("RUN_URL", "(run CI non renseigné)")

    github = _build_github_client(github_token, repository, api_url)
    jira = _build_jira_client(jira_base_url, jira_email, jira_token)
    try:
        report = run(github, jira, project_key, issuetype, run_url)
    finally:
        github.close()
        jira.close()

    print(
        f"Résumé : {len(report.created)} créé(s), {len(report.skipped)} déjà tracé(s), "
        f"catégories indisponibles : {report.unavailable or 'aucune'}."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
