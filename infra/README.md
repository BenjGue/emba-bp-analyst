# Infra — Provisionnement Azure

> Scripts de provisionnement de l'environnement Azure pour BizPlan-IA.

## Lancer le provisionnement

```bash
# Environnement dev (défaut)
bash infra/provision.sh

# Passer des paramètres explicites
bash infra/provision.sh dev westeurope
```

**Pré-requis :** Azure CLI installé + `az login` effectué avec un compte Contributor.

## Ressources créées

Toutes les ressources sont dans **un seul Resource Group** `rg-bizplan-dev` pour faciliter le nettoyage.

| Ressource | Nom | Rôle |
|---|---|---|
| Resource Group | `rg-bizplan-dev` | Conteneur unique de toutes les ressources |
| Container Registry | `acrbizplandev` | Images Docker |
| MySQL Flexible Server | `bizplan-mysql-dev` | Base de données |
| Key Vault | `bizplan-kv-dev` | Secrets (DATABASE_URL, clés API) |
| Container Apps Env | `bizplan-env-dev` | Runtime des containers |
| Container App | `bizplan-api-dev` | API FastAPI |

## Supprimer toutes les ressources

```bash
az group delete --name rg-bizplan-dev --yes --no-wait
```

Une seule commande supprime **tout** sans laisser de ressources orphelines.

## Après le provisionnement

1. Copier les valeurs affichées (`AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`) dans **GitHub → Settings → Secrets → Actions**
2. Récupérer la `DATABASE_URL` depuis Key Vault pour `.env.local` :
   ```bash
   az keyvault secret show --vault-name bizplan-kv-dev --name DATABASE-URL --query value -o tsv
   ```
