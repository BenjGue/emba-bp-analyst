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

## Autorisation du pull ACR par le Container App (identité managée)

Le Container App tire son image depuis l'ACR via une **identité managée system-assigned**
(et non un mot de passe admin). Ces 3 étapes sont nécessaires une fois après le premier
provisionnement — sinon le déploiement échoue avec `UNAUTHORIZED: authentication required` :

```bash
# 1. Activer l'identité managée sur le Container App
PRINCIPAL_ID=$(az containerapp identity assign \
  --name bizplan-api-dev --resource-group rg-bizplan-dev \
  --system-assigned --query principalId -o tsv)

# 2. Donner le rôle AcrPull à cette identité sur l'ACR
ACR_ID=$(az acr show --name acrbizplandev --resource-group rg-bizplan-dev --query id -o tsv)
az role assignment create \
  --assignee-object-id "$PRINCIPAL_ID" --assignee-principal-type ServicePrincipal \
  --role AcrPull --scope "$ACR_ID"

# 3. Lier le registre au Container App via cette identité
az containerapp registry set \
  --name bizplan-api-dev --resource-group rg-bizplan-dev \
  --server acrbizplandev.azurecr.io --identity system
```

## Dépannage du pipeline de déploiement

| Symptôme | Cause | Correctif appliqué |
|---|---|---|
| Étape « Download SSL cert » en échec (exit 60) | `curl` ne peut pas vérifier le certificat de l'hôte de téléchargement | Le certificat `DigiCertGlobalRootG2.crt.pem` est **versionné dans le repo** ; l'étape `curl` a été retirée de `deploy.yml` |
| Déploiement Container App `UNAUTHORIZED: authentication required` | Le Container App n'a pas le droit de tirer l'image ACR | Identité managée + rôle **AcrPull** + `az containerapp registry set --identity system` (voir section ci-dessus) |
| Azure login OIDC `exit 60` quand le job utilise `environment: dev` | Le sujet du token OIDC devient `repo:OWNER/REPO:environment:dev` | Ajout d'un *federated credential* avec ce sujet sur l'app registration |
