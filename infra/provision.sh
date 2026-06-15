#!/usr/bin/env bash
# =============================================================================
# infra/provision.sh — Provisionnement complet de l'environnement Azure
#
# Usage :
#   ./infra/provision.sh [--env dev|prod] [--location westeurope]
#
# Pré-requis :
#   - Azure CLI connecté : az login
#   - Droits Contributor sur la souscription
#
# Tout est dans un seul Resource Group → suppression en une commande :
#   az group delete --name rg-bizplan-dev --yes --no-wait
# =============================================================================

set -euo pipefail

# ── Paramètres (modifiables) ─────────────────────────────────────────────────
ENV="${1:-dev}"                          # dev | prod
LOCATION="${2:-westeurope}"
PROJECT="bizplan"

RG="rg-${PROJECT}-${ENV}"               # rg-bizplan-dev
ACR="acr${PROJECT}${ENV}"               # acrbizplandev (pas de tirets autorisés)
MYSQL_SERVER="${PROJECT}-mysql-${ENV}"  # bizplan-mysql-dev
MYSQL_DB="bizplan"
MYSQL_ADMIN="bizplanadmin"
ACA_ENV="${PROJECT}-env-${ENV}"         # bizplan-env-dev
ACA_APP="${PROJECT}-api-${ENV}"         # bizplan-api-dev
KEYVAULT="${PROJECT}-kv-${ENV}"         # bizplan-kv-dev

echo "============================================================"
echo "  BizPlan-IA — Provisionnement Azure"
echo "  Environnement : ${ENV}"
echo "  Région        : ${LOCATION}"
echo "  Resource Group: ${RG}"
echo "============================================================"
echo ""

# ── 0. Vérifications ─────────────────────────────────────────────────────────
command -v az &>/dev/null || { echo "❌ Azure CLI non installé."; exit 1; }
az account show &>/dev/null || { echo "❌ Non connecté. Lancer : az login"; exit 1; }

SUBSCRIPTION_ID=$(az account show --query id -o tsv)
echo "✅ Souscription : ${SUBSCRIPTION_ID}"

# ── 1. Resource Group ────────────────────────────────────────────────────────
echo ""
echo "▶ 1/7 — Resource Group"
az group create \
    --name "${RG}" \
    --location "${LOCATION}" \
    --tags projet=bizplan-ia env="${ENV}" equipe="emba-epitech-p2026" \
    --output none
echo "   ✅ ${RG} créé dans ${LOCATION}"

# ── 2. Azure Container Registry ──────────────────────────────────────────────
echo ""
echo "▶ 2/7 — Azure Container Registry"
if az acr show --name "${ACR}" --resource-group "${RG}" &>/dev/null; then
    echo "   ℹ️  ${ACR} existe déjà"
else
    az acr create \
        --resource-group "${RG}" \
        --name "${ACR}" \
        --sku Basic \
        --admin-enabled false \
        --output none
fi
echo "   ✅ ${ACR}.azurecr.io"

# ── 3. Key Vault ─────────────────────────────────────────────────────────────
echo ""
echo "▶ 3/7 — Key Vault"
if az keyvault show --name "${KEYVAULT}" &>/dev/null; then
    echo "   ℹ️  ${KEYVAULT} existe déjà"
else
    az keyvault create \
        --resource-group "${RG}" \
        --name "${KEYVAULT}" \
        --location "${LOCATION}" \
        --enable-rbac-authorization true \
        --retention-days 7 \
        --output none
fi
echo "   ✅ ${KEYVAULT}"

# ── 4. MySQL Flexible Server ──────────────────────────────────────────────────
echo ""
echo "▶ 4/7 — MySQL Flexible Server"

# Générer un mot de passe aléatoire et le stocker dans Key Vault
MYSQL_PASSWORD=$(openssl rand -base64 32 | tr -d '/+=' | head -c 32)

if az mysql flexible-server show --resource-group "${RG}" --name "${MYSQL_SERVER}" &>/dev/null; then
    echo "   ℹ️  ${MYSQL_SERVER} existe déjà — réinitialisation du mot de passe admin"
    az mysql flexible-server update \
        --resource-group "${RG}" \
        --name "${MYSQL_SERVER}" \
        --admin-password "${MYSQL_PASSWORD}" \
        --output none
else
    az mysql flexible-server create \
        --resource-group "${RG}" \
        --name "${MYSQL_SERVER}" \
        --location "${LOCATION}" \
        --admin-user "${MYSQL_ADMIN}" \
        --admin-password "${MYSQL_PASSWORD}" \
        --sku-name "Standard_B1ms" \
        --tier "Burstable" \
        --storage-size 20 \
        --version 8.0.21 \
        --high-availability Disabled \
        --backup-retention 7 \
        --yes \
        --output none
fi

# Base de données
az mysql flexible-server db create \
    --resource-group "${RG}" \
    --server-name "${MYSQL_SERVER}" \
    --database-name "${MYSQL_DB}" \
    --output none

# Règle firewall : autoriser les Azure services
az mysql flexible-server firewall-rule create \
    --resource-group "${RG}" \
    --name "${MYSQL_SERVER}" \
    --rule-name AllowAzureServices \
    --start-ip-address 0.0.0.0 \
    --end-ip-address 0.0.0.0 \
    --output none

MYSQL_HOST="${MYSQL_SERVER}.mysql.database.azure.com"
# ssl_ca pointe sur le bundle d'autorités du système (image Debian slim), qui
# contient « DigiCert Global Root G2 » utilisé par Azure Database for MySQL.
# (Ne pas référencer un fichier .pem relatif : il n'existe pas dans l'image.)
DB_URL="mysql+pymysql://${MYSQL_ADMIN}:${MYSQL_PASSWORD}@${MYSQL_HOST}/${MYSQL_DB}?ssl_ca=/etc/ssl/certs/ca-certificates.crt"

echo "   ✅ ${MYSQL_HOST}"

# Stocker la connection string dans Key Vault
az keyvault secret set \
    --vault-name "${KEYVAULT}" \
    --name "DATABASE-URL" \
    --value "${DB_URL}" \
    --output none
echo "   ✅ DATABASE-URL stocké dans Key Vault"

# ── 5. Container Apps Environment ────────────────────────────────────────────
echo ""
echo "▶ 5/7 — Container Apps Environment"
if az containerapp env show --resource-group "${RG}" --name "${ACA_ENV}" &>/dev/null; then
    echo "   ℹ️  ${ACA_ENV} existe déjà"
else
    az containerapp env create \
        --resource-group "${RG}" \
        --name "${ACA_ENV}" \
        --location "${LOCATION}" \
        --output none
fi
echo "   ✅ ${ACA_ENV}"

# ── 6. Container App (déploiement initial vide) ───────────────────────────────
echo ""
echo "▶ 6/7 — Container App"
if az containerapp show --resource-group "${RG}" --name "${ACA_APP}" &>/dev/null; then
    echo "   ℹ️  ${ACA_APP} existe déjà"
else
    az containerapp create \
        --resource-group "${RG}" \
        --name "${ACA_APP}" \
        --environment "${ACA_ENV}" \
        --image "mcr.microsoft.com/azuredocs/containerapps-helloworld:latest" \
        --target-port 8000 \
        --ingress external \
        --min-replicas 0 \
        --max-replicas 3 \
        --cpu 0.5 \
        --memory 1.0Gi \
        --output none
fi
echo "   ✅ ${ACA_APP} (image placeholder — sera remplacée par CI/CD)"

# ── 6b. Persistance prod : DATABASE_URL (BIZ-29 / BIZ-41) ─────────────────────
# La connection string MySQL est stockée dans Key Vault (secret DATABASE-URL)
# comme source de vérité. Pour le câblage effectif de la Container App, on pose
# un secret applicatif `database-url` *directement* à partir de la valeur connue
# ici (DB_URL) : c'est idempotent et fonctionne même si l'accès public du Key
# Vault est désactivé (pas de dépendance à une Key Vault reference ni à un
# endpoint privé). Aucun secret n'apparaît en clair dans la configuration : il
# est masqué dans le store de secrets de la Container App.
echo ""
echo "▶ 6b/7 — Branchement DATABASE_URL (secret Container App)"

# 1. Identité managée affectée par le système (utile pour d'autres usages)
az containerapp identity assign \
    --resource-group "${RG}" \
    --name "${ACA_APP}" \
    --system-assigned \
    --output none

# 2. Secret applicatif `database-url` posé directement (idempotent)
az containerapp secret set \
    --resource-group "${RG}" \
    --name "${ACA_APP}" \
    --secrets "database-url=${DB_URL}" \
    --output none

# 3. Exposer le secret en variable d'environnement DATABASE_URL
az containerapp update \
    --resource-group "${RG}" \
    --name "${ACA_APP}" \
    --set-env-vars "DATABASE_URL=secretref:database-url" \
    --output none
echo "   ✅ DATABASE_URL branché (secret Container App → MySQL persistant)"

# ── 7. OIDC — Federated credentials pour GitHub Actions ──────────────────────
echo ""
echo "▶ 7/7 — OIDC / Federated credentials GitHub Actions"

# Récupérer l'Object ID du service principal courant ou en créer un
APP_NAME="sp-${PROJECT}-github-${ENV}"
APP_ID=$(az ad app list --display-name "${APP_NAME}" --query "[0].appId" -o tsv 2>/dev/null || true)
if [ -z "${APP_ID}" ]; then
    APP_ID=$(az ad app create --display-name "${APP_NAME}" --query appId -o tsv 2>/dev/null || true)
fi

if [ -z "${APP_ID}" ]; then
    echo "   ⚠️  Impossible de créer l'app registration automatiquement (droits insuffisants)."
    echo "   → Créer manuellement dans Azure AD et ajouter les secrets GitHub :"
    echo "      AZURE_CLIENT_ID, AZURE_TENANT_ID, AZURE_SUBSCRIPTION_ID"
else
    SP_OBJECT_ID=$(az ad sp show --id "${APP_ID}" --query id -o tsv 2>/dev/null || true)
    if [ -z "${SP_OBJECT_ID}" ]; then
        SP_OBJECT_ID=$(az ad sp create --id "${APP_ID}" --query id -o tsv)
    fi

    # Federated credential pour la branche main (idempotent)
    if ! az ad app federated-credential list --id "${APP_ID}" --query "[?name=='github-main']" -o tsv | grep -q .; then
        az ad app federated-credential create \
            --id "${APP_ID}" \
            --parameters "{
                \"name\": \"github-main\",
                \"issuer\": \"https://token.actions.githubusercontent.com\",
                \"subject\": \"repo:BenjGue/emba-bp-analyst:ref:refs/heads/main\",
                \"audiences\": [\"api://AzureADTokenExchange\"]
            }" \
            --output none
    fi

    # Rôle Contributor sur le Resource Group (idempotent)
    az role assignment create \
        --assignee "${SP_OBJECT_ID}" \
        --role "Contributor" \
        --scope "/subscriptions/${SUBSCRIPTION_ID}/resourceGroups/${RG}" \
        --output none 2>/dev/null || true

    # Rôle AcrPush sur l'ACR (idempotent)
    ACR_ID=$(az acr show --name "${ACR}" --resource-group "${RG}" --query id -o tsv)
    az role assignment create \
        --assignee "${SP_OBJECT_ID}" \
        --role "AcrPush" \
        --scope "${ACR_ID}" \
        --output none 2>/dev/null || true

    echo "   ✅ App registration : ${APP_NAME} (${APP_ID})"
    echo ""
    echo "   ── Secrets à ajouter dans GitHub Settings → Secrets → Actions ──"
    echo "   AZURE_CLIENT_ID      = ${APP_ID}"
    echo "   AZURE_TENANT_ID      = $(az account show --query tenantId -o tsv)"
    echo "   AZURE_SUBSCRIPTION_ID= ${SUBSCRIPTION_ID}"
fi

# ── Résumé ────────────────────────────────────────────────────────────────────
echo ""
echo "============================================================"
echo "  ✅ Provisionnement terminé"
echo "============================================================"
echo ""
echo "  Resource Group  : ${RG}"
echo "  ACR             : ${ACR}.azurecr.io"
echo "  MySQL           : ${MYSQL_HOST}"
echo "  Container App   : ${ACA_APP}"
echo "  Key Vault       : ${KEYVAULT}"
echo ""
echo "  ⚠️  Pour supprimer TOUTES les ressources en une commande :"
echo "     az group delete --name ${RG} --yes --no-wait"
echo ""
