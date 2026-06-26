"""Tests unitaires du calcul des scénarios financiers (BIZ-85).

Vérifie que le délai de retour sur investissement honore le délai de
rentabilité issu des données (profil mensuel réel ou saisie) au lieu d'un
recalcul annualisé qui ignorerait l'horizon réel.
"""

from __future__ import annotations

from app.services.generation import _build_scenarios


def test_payback_median_egale_delai_rentabilite_des_donnees() -> None:
    """Le payback médian reprend exactement le délai de rentabilité fourni."""
    scenarios = _build_scenarios(
        investissement=9000.0,
        revenus=140400.0,
        couts=120000.0,
        delai_rentabilite_mois=19,
    )
    assert scenarios["median"]["retour_investissement_mois"] == 19.0


def test_payback_respecte_l_ordre_bas_median_haut() -> None:
    """Un résultat net plus élevé (scénario haut) raccourcit le payback."""
    scenarios = _build_scenarios(
        investissement=100000.0,
        revenus=80000.0,
        couts=30000.0,
        delai_rentabilite_mois=36,
    )
    bas = scenarios["bas"]["retour_investissement_mois"]
    median = scenarios["median"]["retour_investissement_mois"]
    haut = scenarios["haut"]["retour_investissement_mois"]
    assert median == 36.0
    assert bas > median > haut


def test_payback_negatif_si_scenario_non_rentable() -> None:
    """Un scénario à résultat net négatif renvoie -1 (jamais rentable)."""
    scenarios = _build_scenarios(
        investissement=50000.0,
        revenus=20000.0,
        couts=25000.0,
        delai_rentabilite_mois=24,
    )
    assert scenarios["bas"]["retour_investissement_mois"] == -1.0
    assert scenarios["median"]["retour_investissement_mois"] == -1.0


def test_payback_repli_analytique_sans_delai_de_reference() -> None:
    """Sans délai exploitable (0), on retombe sur la formule annualisée."""
    scenarios = _build_scenarios(
        investissement=120000.0,
        revenus=80000.0,
        couts=30000.0,
        delai_rentabilite_mois=0,
    )
    # median : 120000 / (80000 - 30000) * 12 = 28.8
    assert scenarios["median"]["retour_investissement_mois"] == 28.8


def test_scenarios_exposent_bfr_et_tresorerie() -> None:
    """Chaque scénario calcule un BFR estimé et une trésorerie de fin d'année (BIZ-89)."""
    scenarios = _build_scenarios(
        investissement=100000.0,
        revenus=80000.0,
        couts=30000.0,
        delai_rentabilite_mois=36,
    )
    median = scenarios["median"]
    # BFR médian : 80000 / 360 * 30 = 6666.67
    assert median["bfr_estime"] == 6666.67
    # Trésorerie fin d'année 1 : (80000 - 30000) - 100000 - 6666.67 = -56666.67
    assert median["tresorerie_fin_annee"] == -56666.67


def test_bfr_proportionnel_au_chiffre_d_affaires() -> None:
    """Le BFR croît avec le chiffre d'affaires du scénario (BIZ-89)."""
    scenarios = _build_scenarios(
        investissement=100000.0,
        revenus=80000.0,
        couts=30000.0,
        delai_rentabilite_mois=36,
    )
    assert scenarios["bas"]["bfr_estime"] < scenarios["median"]["bfr_estime"]
    assert scenarios["median"]["bfr_estime"] < scenarios["haut"]["bfr_estime"]
