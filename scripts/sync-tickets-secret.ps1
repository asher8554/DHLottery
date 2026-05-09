# 로컬 구매번호 YAML을 GitHub Actions Secret으로 업로드하는 스크립트
[CmdletBinding()]
param(
    [string]$Path = "data/tickets.yml",
    [string]$Repo = "asher8554/DHLottery",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    throw "GitHub CLI(gh) is required. Install it from https://cli.github.com/ and try again."
}

gh auth status *> $null
if ($LASTEXITCODE -ne 0) {
    throw "GitHub CLI login is required. Run gh auth login first."
}

if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
    throw "Ticket file was not found. $Path"
}

$resolvedPath = (Resolve-Path -LiteralPath $Path).Path
$content = Get-Content -LiteralPath $resolvedPath -Raw -Encoding UTF8

if ([string]::IsNullOrWhiteSpace($content)) {
    throw "Ticket file is empty. $resolvedPath"
}

if ($content -notmatch "(?m)^\s*(lotto|pension)\s*:") {
    Write-Warning "Could not find a lotto or pension section. Check the YAML format."
}

if ($DryRun) {
    Write-Host "Dry run passed. Secret was not updated. $resolvedPath"
    return
}

$content | gh secret set TICKETS_YAML --repo $Repo
if ($LASTEXITCODE -ne 0) {
    throw "Failed to upload TICKETS_YAML secret."
}

Write-Host "TICKETS_YAML secret was updated. $Repo"
