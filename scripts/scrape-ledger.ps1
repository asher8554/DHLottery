# 로컬 브라우저에서 동행복권 구매내역을 가져오는 스크립트
[CmdletBinding()]
param(
    [string]$Path = "data/tickets.yml",
    [string]$ProfileDir = ".browser/dhlottery",
    [string]$EnvFile = ".env",
    [string]$LoginUrl = "https://www.dhlottery.co.kr/login",
    [int]$MaxTickets = 30,
    [switch]$Append,
    [switch]$Headless,
    [switch]$ShowProgress
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot
try {
    $arguments = @(
        "-m", "dhlottery_checker", "scrape-ledger",
        "--tickets", $Path,
        "--profile-dir", $ProfileDir,
        "--env-file", $EnvFile,
        "--login-url", $LoginUrl,
        "--max-tickets", [string]$MaxTickets
    )
    if ($Append) {
        $arguments += "--append"
    }
    if ($Headless) {
        $arguments += "--headless"
    }
    if ($ShowProgress -or $PSBoundParameters.ContainsKey("Verbose")) {
        $arguments += "--verbose"
    }

    python @arguments
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
} finally {
    Pop-Location
}
