"""Sonde de tests exploratoires (négatifs + limites) contre l'API déployée.

Lance une batterie d'assertions sur les règles de validation, les codes
d'erreur et la logique métier décrites dans les schémas/backlog, et imprime un
rapport PASS/FAIL exploitable pour le reporting de bugs.

Usage:
    python scripts/api_probe.py [base_url]
"""

from __future__ import annotations

import json
import sys

import httpx

BASE = (
    sys.argv[1]
    if len(sys.argv) > 1
    else ("https://bizplan-api-dev.salmondune-1b29666f.westeurope.azurecontainerapps.io")
)

results: list[tuple[str, bool, str]] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    results.append((name, cond, detail))
    flag = "PASS" if cond else "FAIL"
    print(f"[{flag}] {name}" + (f" :: {detail}" if detail else ""))


def main() -> None:
    c = httpx.Client(base_url=BASE, timeout=30.0)

    # --- Health ---------------------------------------------------------------
    r = c.get("/health")
    check("health 200", r.status_code == 200, f"{r.status_code}")

    # --- Création projet : validations ---------------------------------------
    valid = {
        "nom": "Probe projet",
        "description": "Description de test exploratoire valide.",
        "direction": "Numérique",
        "duree_estimee_mois": 12,
    }

    r = c.post("/projects", json={**valid, "nom": ""})
    check("create nom vide -> 422", r.status_code == 422, f"{r.status_code}")

    r = c.post("/projects", json={**valid, "nom": "x" * 201})
    check("create nom 201 car -> 422", r.status_code == 422, f"{r.status_code}")

    r = c.post("/projects", json={**valid, "description": "y" * 1001})
    check("create desc 1001 car -> 422", r.status_code == 422, f"{r.status_code}")

    r = c.post("/projects", json={**valid, "duree_estimee_mois": 0})
    check("create duree 0 -> 422", r.status_code == 422, f"{r.status_code}")

    r = c.post("/projects", json={**valid, "duree_estimee_mois": 601})
    check("create duree 601 -> 422", r.status_code == 422, f"{r.status_code}")

    r = c.post("/projects", json={**valid, "duree_estimee_mois": -5})
    check("create duree negative -> 422", r.status_code == 422, f"{r.status_code}")

    r = c.post("/projects", json={**valid, "direction": "Direction Bidon"})
    check("create direction invalide -> 422", r.status_code == 422, f"{r.status_code}")

    r = c.post("/projects", json={"nom": "x"})
    check("create champs manquants -> 422", r.status_code == 422, f"{r.status_code}")

    # XSS / HTML injection dans le nom (doit être stocké tel quel et échappé en UI)
    r = c.post("/projects", json={**valid, "nom": "<script>alert(1)</script>"})
    check("create nom avec HTML accepté (échappé en UI)", r.status_code == 201, f"{r.status_code}")
    xss_id = r.json().get("id") if r.status_code == 201 else None

    # --- Création projet valide ----------------------------------------------
    r = c.post("/projects", json=valid)
    check("create projet valide -> 201", r.status_code == 201, f"{r.status_code}")
    pid = r.json()["id"] if r.status_code == 201 else None

    # --- 404 sur ressources inexistantes -------------------------------------
    r = c.get("/projects/999999")
    check("get projet inexistant -> 404", r.status_code == 404, f"{r.status_code}")

    r = c.get("/projects/999999/score")
    check("get score inexistant -> 404", r.status_code == 404, f"{r.status_code}")

    r = c.get("/projects/999999/bp")
    check("get bp inexistant -> 404", r.status_code == 404, f"{r.status_code}")

    r = c.post("/projects/999999/generate")
    check("generate projet inexistant -> 404", r.status_code == 404, f"{r.status_code}")

    r = c.delete("/projects/999999")
    check("delete projet inexistant -> 404", r.status_code == 404, f"{r.status_code}")

    # id non entier
    r = c.get("/projects/abc")
    check("get projet id non entier -> 422", r.status_code == 422, f"{r.status_code}")

    if pid is not None:
        # --- Financials validations ------------------------------------------
        fin_ok = {
            "investissement_initial": 100000,
            "revenus_annuels": 80000,
            "couts_annuels": 30000,
            "delai_rentabilite_mois": 36,
        }
        r = c.put(f"/projects/{pid}/financials", json={**fin_ok, "investissement_initial": -1})
        check("financials invest negatif -> 422", r.status_code == 422, f"{r.status_code}")

        r = c.put(f"/projects/{pid}/financials", json={**fin_ok, "delai_rentabilite_mois": 0})
        check("financials delai 0 -> 422", r.status_code == 422, f"{r.status_code}")

        r = c.put(f"/projects/{pid}/financials", json={**fin_ok, "delai_rentabilite_mois": 601})
        check("financials delai 601 -> 422", r.status_code == 422, f"{r.status_code}")

        # generate sans financials (nouveau projet) -> 400
        r2 = c.post("/projects", json=valid)
        pid_nofin = r2.json()["id"]
        r = c.post(f"/projects/{pid_nofin}/generate")
        check("generate sans financials -> 400", r.status_code == 400, f"{r.status_code}")
        c.delete(f"/projects/{pid_nofin}")

        # financials valides
        r = c.put(f"/projects/{pid}/financials", json=fin_ok)
        check("financials valides -> 200", r.status_code == 200, f"{r.status_code}")

        # --- Dimensions / score validations ----------------------------------
        dims_ok = {
            "rentabilite": 5,
            "alignement": 5,
            "risque": 5,
            "impact_operationnel": 5,
            "impact_social": 5,
            "faisabilite": 5,
        }
        r = c.put(f"/projects/{pid}/dimensions", json={**dims_ok, "rentabilite": 11})
        check("dimension 11 (>10) -> 422", r.status_code == 422, f"{r.status_code}")

        r = c.put(f"/projects/{pid}/dimensions", json={**dims_ok, "rentabilite": -1})
        check("dimension -1 -> 422", r.status_code == 422, f"{r.status_code}")

        bad = dict(dims_ok)
        del bad["faisabilite"]
        r = c.put(f"/projects/{pid}/dimensions", json=bad)
        check("dimension manquante -> 422", r.status_code == 422, f"{r.status_code}")

        # --- Score métier : toutes notes à 0 -> 0 ----------------------------
        dims0 = dict.fromkeys(dims_ok, 0)
        r = c.put(f"/projects/{pid}/dimensions", json=dims0)
        if r.status_code == 200:
            total0 = r.json()["total"]
            check("score toutes notes 0 == 0", abs(total0 - 0) < 0.01, f"total={total0}")
        else:
            check("score toutes notes 0 == 0", False, f"HTTP {r.status_code}")

        # toutes notes à 10 -> 100
        dims10 = dict.fromkeys(dims_ok, 10)
        r = c.put(f"/projects/{pid}/dimensions", json=dims10)
        if r.status_code == 200:
            total10 = r.json()["total"]
            check("score toutes notes 10 == 100", abs(total10 - 100) < 0.01, f"total={total10}")
        else:
            check("score toutes notes 10 == 100", False, f"HTTP {r.status_code}")

        # remettre dims valides milieu
        c.put(f"/projects/{pid}/dimensions", json=dims_ok)

        # --- Génération + export ---------------------------------------------
        r = c.post(f"/projects/{pid}/generate")
        check("generate avec financials -> 201", r.status_code == 201, f"{r.status_code}")

        r = c.get(f"/projects/{pid}/export?format=md")
        check("export md -> 200", r.status_code == 200, f"{r.status_code}")

        r = c.get(f"/projects/{pid}/export?format=pdf")
        check(
            "export pdf -> 200",
            r.status_code == 200,
            f"{r.status_code} ct={r.headers.get('content-type', '')}",
        )

        r = c.get(f"/projects/{pid}/export?format=docx")
        check("export format invalide -> 4xx", 400 <= r.status_code < 500, f"{r.status_code}")

        # --- draft-description (IA désactivée -> 503 attendu) ----------------
        r = c.post(
            "/projects/draft-description",
            json={"idees": "casiers connectés bureau de poste", "direction": "Numérique"},
        )
        check("draft-description IA off -> 503", r.status_code == 503, f"{r.status_code}")

        # --- Import Excel : fichier invalide ---------------------------------
        r = c.post(
            f"/projects/{pid}/financials/import",
            files={"file": ("fake.xlsx", b"not a real xlsx", "application/vnd.ms-excel")},
        )
        check("import xlsx corrompu -> 422", r.status_code == 422, f"{r.status_code}")

        r = c.post(
            f"/projects/{pid}/financials/import",
            files={"file": ("data.txt", b"hello", "text/plain")},
        )
        check("import non-xlsx -> 422/400", r.status_code in (400, 422), f"{r.status_code}")

        # cleanup
        c.delete(f"/projects/{pid}")

    if xss_id is not None:
        c.delete(f"/projects/{xss_id}")

    # --- Résumé ---------------------------------------------------------------
    print("\n" + "=" * 60)
    passed = sum(1 for _, ok, _ in results if ok)
    failed = [(n, d) for n, ok, d in results if not ok]
    print(f"TOTAL: {passed}/{len(results)} PASS, {len(failed)} FAIL")
    if failed:
        print("\nFAILURES:")
        for n, d in failed:
            print(f"  - {n} :: {d}")
    print("=" * 60)
    # JSON machine-readable
    print(
        "\nJSON_RESULTS="
        + json.dumps([{"name": n, "pass": ok, "detail": d} for n, ok, d in results])
    )


if __name__ == "__main__":
    main()
