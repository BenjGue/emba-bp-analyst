# Pricing — Suivi du coût des requêtes IA

> Suivi estimatif du coût de chaque échange avec Claude Sonnet 4.6 dans ce projet.  
> **Important** : les chiffres sont des **estimations** — je n'ai pas accès aux compteurs de tokens exacts. Les coûts réels peuvent varier de ±20%.

---

## Modèle de tarification — Claude Sonnet 4.6 (Anthropic API)

| Type | Prix |
|---|---|
| **Input tokens** (contexte + message) | $3,00 / 1M tokens |
| **Output tokens** (réponse générée) | $15,00 / 1M tokens |

> Le coût d'input **croît à chaque tour** car le contexte complet (historique + fichiers ouverts + mémoire) est renvoyé à chaque requête.

---

## Session du 2026-06-12

| # | Requête (résumé) | Input estimé | Output estimé | Coût input | Coût output | **Total** |
|---|---|---|---|---|---|---|
| 1 | Créer compte GitHub Copilot Enterprise via Azure | ~3 000 tok | ~600 tok | $0,009 | $0,009 | **$0,018** |
| 2 | Update craftsmanship.md : choix Claude Code vs Copilot Education | ~6 000 tok | ~1 200 tok | $0,018 | $0,018 | **$0,036** |
| 3 | Qu'est-ce qui a déjà été créé niveau craftsmanship ? | ~8 000 tok | ~300 tok | $0,024 | $0,005 | **$0,029** |
| 4 | Créer fichier TODO.md multi-rubriques | ~9 000 tok | ~1 500 tok | $0,027 | $0,023 | **$0,050** |
| 5 | Update How-to-setup.md avec dernières infos | ~12 000 tok | ~2 500 tok | $0,036 | $0,038 | **$0,074** |
| 6 | How-to-setup : détailler assistant IA, Azure par Brice, pas de MySQL local | ~16 000 tok | ~2 800 tok | $0,048 | $0,042 | **$0,090** |
| 7 | Commit & push toutes les modifications | ~18 000 tok | ~500 tok | $0,054 | $0,008 | **$0,062** |
| 8 | Commit & push (working tree clean) | ~18 500 tok | ~150 tok | $0,056 | $0,002 | **$0,058** |
| 9 | How-to-setup : repo privé + ajout collaborateur | ~19 000 tok | ~400 tok | $0,057 | $0,006 | **$0,063** |
| 10 | Correction : c'est Benjamin (pas Brice) qui ajoute Mauricette | ~19 500 tok | ~150 tok | $0,059 | $0,002 | **$0,061** |
| 11 | Commit & push | ~20 000 tok | ~200 tok | $0,060 | $0,003 | **$0,063** |
| 12 | Créer fichier pricing.md + explications coût | ~20 500 tok | ~1 000 tok | $0,062 | $0,015 | **$0,077** |

### Totaux session

| | Valeur |
|---|---|
| **Input total estimé** | ~169 500 tokens |
| **Output total estimé** | ~11 300 tokens |
| **Coût input** | ~$0,51 |
| **Coût output** | ~$0,17 |
| **💰 Total session estimé** | **~$0,68** |

---

## Ce qui fait grossir la facture

1. **Le contexte système** : chaque requête inclut les instructions de l'agent (~3 000 tokens fixes)
2. **Les fichiers ouverts dans l'éditeur** : le contenu du fichier actif est joint à chaque message
3. **L'historique de conversation** : chaque tour inclut tous les échanges précédents
4. **Les lectures de fichiers** : chaque `read_file` ajoute du contenu en input

## Conseils pour optimiser

- Démarrer une **nouvelle session** pour un nouveau sujet (repart à 0 sur le contexte)
- Éviter de garder de **grands fichiers ouverts** dans l'éditeur si non nécessaire
- Regrouper plusieurs petites demandes en **une seule requête**

---

*Mis à jour automatiquement à chaque requête de la session.*
