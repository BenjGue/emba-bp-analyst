param(
    [Parameter(Mandatory = $true)][string]$IssueKey,
    [Parameter(Mandatory = $true)][string]$CommentJsonPath
)

$ErrorActionPreference = "Stop"
$email = [Environment]::GetEnvironmentVariable("JIRA_EMAIL", "User")
$token = [Environment]::GetEnvironmentVariable("JIRA_API_TOKEN", "User")
$b64 = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("$email`:$token"))
$headers = @{ Authorization = "Basic $b64"; "Content-Type" = "application/json" }
$base = "https://ionis-stm-team-ek7kwlup.atlassian.net"
$body = Get-Content -Raw -Path $CommentJsonPath
Invoke-RestMethod -Uri "$base/rest/api/3/issue/$IssueKey/comment" -Method Post -Headers $headers -Body $body | Out-Null
Write-Host "$IssueKey -> commentaire ajoute"
