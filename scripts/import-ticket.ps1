# 클립보드의 동행복권 티켓 보기 텍스트를 구매번호 YAML에 반영하는 스크립트
[CmdletBinding()]
param(
    [string]$Path = "data/tickets.yml",
    [switch]$ReplaceAll,
    [switch]$ReplaceLotto,
    [switch]$SyncSecret
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot
try {
    $clipboard = Get-Clipboard
    if ($clipboard -is [array]) {
        $text = $clipboard -join [Environment]::NewLine
    } else {
        $text = [string]$clipboard
    }

    if ([string]::IsNullOrWhiteSpace($text)) {
        throw "Clipboard text is empty. Copy the ticket view text first."
    }

    $tempFile = New-TemporaryFile
    Set-Content -LiteralPath $tempFile -Value $text -Encoding UTF8

    $arguments = @("-m", "dhlottery_checker", "import-ticket", "--input", $tempFile, "--tickets", $Path)
    if ($ReplaceAll) {
        $arguments += "--replace-all"
    }
    if ($ReplaceLotto) {
        $arguments += "--replace-lotto"
    }

    try {
        python @arguments
        if ($LASTEXITCODE -ne 0) {
            exit $LASTEXITCODE
        }
    } finally {
        Remove-Item -LiteralPath $tempFile -ErrorAction SilentlyContinue
    }

    if ($SyncSecret) {
        & "$PSScriptRoot\sync-tickets-secret.ps1" -Path $Path
    }
} finally {
    Pop-Location
}
