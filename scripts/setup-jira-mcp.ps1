#Requires -Version 5.1
<#
.SYNOPSIS
    Configure les variables d'environnement Windows nécessaires au serveur MCP Jira.

.DESCRIPTION
    Ce script définit JIRA_EMAIL et JIRA_API_TOKEN en tant que variables d'environnement
    persistantes au niveau de l'utilisateur Windows (HKCU). Ces variables sont lues par
    VS Code au démarrage pour alimenter le serveur MCP Atlassian (atlassian-mcp@latest).

    Prérequis : générer un token API sur https://id.atlassian.com/manage-api-tokens

.EXAMPLE
    .\scripts\setup-jira-mcp.ps1
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "=== Configuration MCP Jira — BizPlan-IA ===" -ForegroundColor Cyan
Write-Host ""

# ── Récupération de l'email ──────────────────────────────────────────────────
$existingEmail = [System.Environment]::GetEnvironmentVariable("JIRA_EMAIL", "User")
if ($existingEmail) {
    Write-Host "JIRA_EMAIL actuel : $existingEmail"
    $changeEmail = Read-Host "Conserver cette valeur ? [O/n]"
    if ($changeEmail -eq "n" -or $changeEmail -eq "N") {
        $jiraEmail = Read-Host "Nouvel email Atlassian"
    } else {
        $jiraEmail = $existingEmail
    }
} else {
    $jiraEmail = Read-Host "Email Atlassian (ex: prenom.nom@ionis-stm.com)"
}

if (-not $jiraEmail) {
    Write-Error "L'email ne peut pas être vide."
    exit 1
}

# ── Récupération du token ────────────────────────────────────────────────────
Write-Host ""
Write-Host "Générez votre token sur : https://id.atlassian.com/manage-api-tokens" -ForegroundColor Yellow
$existingToken = [System.Environment]::GetEnvironmentVariable("JIRA_API_TOKEN", "User")
if ($existingToken -and $existingToken -ne "<token_atlassian>" -and $existingToken -ne "<ton-token-atlassian>") {
    Write-Host "JIRA_API_TOKEN : déjà défini (valeur masquée)"
    $changeToken = Read-Host "Remplacer le token existant ? [o/N]"
    if ($changeToken -eq "o" -or $changeToken -eq "O") {
        $jiraToken = Read-Host "Nouveau token API Atlassian" -AsSecureString
        $jiraToken = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
            [Runtime.InteropServices.Marshal]::SecureStringToBSTR($jiraToken)
        )
    } else {
        $jiraToken = $existingToken
    }
} else {
    $jiraToken = Read-Host "Token API Atlassian" -AsSecureString
    $jiraToken = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
        [Runtime.InteropServices.Marshal]::SecureStringToBSTR($jiraToken)
    )
}

if (-not $jiraToken -or $jiraToken -eq "<token_atlassian>" -or $jiraToken -eq "<ton-token-atlassian>") {
    Write-Error "Token invalide ou vide. Veuillez générer un vrai token sur https://id.atlassian.com/manage-api-tokens"
    exit 1
}

# ── Persistance au niveau utilisateur Windows ────────────────────────────────
[System.Environment]::SetEnvironmentVariable("JIRA_EMAIL",     $jiraEmail, "User")
[System.Environment]::SetEnvironmentVariable("JIRA_API_TOKEN", $jiraToken, "User")

Write-Host ""
Write-Host "✅  Variables définies avec succès (niveau utilisateur Windows) :" -ForegroundColor Green
Write-Host "   JIRA_EMAIL     = $jiraEmail"
Write-Host "   JIRA_API_TOKEN = ****"
Write-Host ""
Write-Host "⚠️  Redémarrez VS Code pour que les variables soient prises en compte." -ForegroundColor Yellow
Write-Host "   Ensuite : Ctrl+Shift+P → 'MCP: Start Server' → 'jira'" -ForegroundColor Yellow
Write-Host ""
