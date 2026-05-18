# setup-secrets.ps1 — Configurer les GitHub Secrets depuis le .env local
# Prérequis : gh auth login effectué + .env présent
# Usage : .\setup-secrets.ps1

$repo = "boutique-oss/jobwatcherfrv2"
$envFile = Join-Path $PSScriptRoot ".env"

if (-not (Test-Path $envFile)) {
    Write-Error ".env introuvable. Copie .env.example vers .env et remplis-le."
    exit 1
}

$secrets = @{}
foreach ($line in Get-Content $envFile) {
    if ($line -match '^\s*#' -or $line -notmatch '=') { continue }
    $parts = $line -split '=', 2
    $key   = $parts[0].Trim()
    $value = $parts[1].Trim()
    if ($key -and $value) { $secrets[$key] = $value }
}

$required = @("SUPABASE_URL","SUPABASE_KEY","FT_CLIENT_ID","FT_CLIENT_SECRET","KEYWORDS","LOCATION")

foreach ($name in $required) {
    if (-not $secrets.ContainsKey($name)) {
        Write-Warning "Variable manquante dans .env : $name — ignorée"
        continue
    }
    $secrets[$name] | gh secret set $name --repo $repo
    Write-Host "OK  $name" -ForegroundColor Green
}

# APEC optionnel
if ($secrets.ContainsKey("APEC_API_KEY") -and $secrets["APEC_API_KEY"]) {
    $secrets["APEC_API_KEY"] | gh secret set APEC_API_KEY --repo $repo
    Write-Host "OK  APEC_API_KEY" -ForegroundColor Green
}

Write-Host "`nSecrets configurés sur $repo" -ForegroundColor Cyan
