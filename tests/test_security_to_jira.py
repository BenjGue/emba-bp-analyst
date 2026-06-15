"""Tests de l'automatisation GHAS → JIRA (BIZ-44).

Aucun appel réseau réel : les API GitHub et JIRA sont simulées via
``httpx.MockTransport``.
"""

from __future__ import annotations

import json

import httpx

from scripts.security_to_jira import (
    SecurityAlert,
    build_description,
    fetch_code_scanning_alerts,
    fetch_dependabot_alerts,
    run,
)


def _github_handler(request: httpx.Request) -> httpx.Response:
    """Simule l'API GitHub : code scanning + dependabot OK, secret scanning 404."""
    path = request.url.path
    if path.endswith("/code-scanning/alerts"):
        return httpx.Response(
            200,
            json=[
                {
                    "number": 12,
                    "html_url": "https://github.com/o/r/security/code-scanning/12",
                    "rule": {
                        "description": "Injection SQL possible",
                        "security_severity_level": "high",
                        "name": "py/sql-injection",
                    },
                    "most_recent_instance": {"message": {"text": "Entrée non filtrée"}},
                }
            ],
        )
    if path.endswith("/secret-scanning/alerts"):
        return httpx.Response(404, json={"message": "Not Found"})
    if path.endswith("/dependabot/alerts"):
        return httpx.Response(
            200,
            json=[
                {
                    "number": 5,
                    "html_url": "https://github.com/o/r/security/dependabot/5",
                    "security_advisory": {"severity": "medium", "summary": "Vuln dans lib"},
                    "dependency": {"package": {"name": "requests"}},
                }
            ],
        )
    return httpx.Response(200, json=[])


def _jira_handler(request: httpx.Request) -> httpx.Response:
    """Simule JIRA : ghas-codescan-12 existe déjà, le reste est créable."""
    path = request.url.path
    if path == "/rest/api/3/search/jql":
        payload = json.loads(request.content.decode())
        if "ghas-codescan-12" in payload["jql"]:
            return httpx.Response(200, json={"issues": [{"key": "BIZ-12"}]})
        return httpx.Response(200, json={"issues": []})
    if path == "/rest/api/3/issue":
        return httpx.Response(201, json={"key": "BIZ-100"})
    return httpx.Response(404, json={})


def _github_client() -> httpx.Client:
    return httpx.Client(
        base_url="https://api.github.com/repos/o/r",
        transport=httpx.MockTransport(_github_handler),
    )


def _jira_client() -> httpx.Client:
    return httpx.Client(
        base_url="https://jira.example.net",
        transport=httpx.MockTransport(_jira_handler),
    )


def test_dedup_label_format() -> None:
    alert = SecurityAlert("codescan", 12, "high", "x", "y", "z")
    assert alert.dedup_label == "ghas-codescan-12"


def test_fetch_code_scanning_alerts_normalise() -> None:
    with _github_client() as client:
        alerts = fetch_code_scanning_alerts(client)
    assert len(alerts) == 1
    assert alerts[0].number == 12
    assert alerts[0].severity == "high"
    assert "Injection" in alerts[0].summary


def test_fetch_dependabot_alerts_normalise() -> None:
    with _github_client() as client:
        alerts = fetch_dependabot_alerts(client)
    assert alerts[0].category == "dep"
    assert "requests" in alerts[0].summary


def test_build_description_inclut_lien_et_run() -> None:
    alert = SecurityAlert("dep", 5, "medium", "Dépendance vulnérable", "détail", "http://x")
    doc = build_description(alert, "http://run")
    flat = json.dumps(doc, ensure_ascii=False)
    assert "http://x" in flat
    assert "http://run" in flat
    assert doc["type"] == "doc"


def test_run_cree_et_dedoublonne() -> None:
    with _github_client() as github, _jira_client() as jira:
        report = run(github, jira, "BIZ", "Tâche", "http://run")
    # code scanning #12 déjà tracé -> ignoré ; dependabot #5 -> créé.
    assert report.created == ["BIZ-100"]
    assert report.skipped == ["ghas-codescan-12"]
    # secret scanning a renvoyé 404 -> catégorie indisponible.
    assert report.unavailable == ["secret-scanning"]
