# 동행복권 구매내역을 가져와 data/tickets.yml을 커밋하고 원격에 올리는 스크립트
[CmdletBinding()]
param(
    [string]$Path = "data/tickets.yml",
    [string]$ProfileDir = ".browser/dhlottery",
    [string]$EnvFile = ".env",
    [string]$LoginUrl = "https://www.dhlottery.co.kr/login",
    [int]$MaxTickets = 30,
    [switch]$Append,
    [switch]$Headless,
    [switch]$ShowProgress,
    [switch]$NoPush,
    [string]$CommitMessage = "구매번호 자동 반영"
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$scrapeScript = Join-Path $PSScriptRoot "scrape-ledger.ps1"

Push-Location $repoRoot
try {
    $scrapeParams = @{
        Path = $Path
        ProfileDir = $ProfileDir
        EnvFile = $EnvFile
        LoginUrl = $LoginUrl
        MaxTickets = $MaxTickets
    }
    if ($Append) {
        $scrapeParams.Append = $true
    }
    if ($Headless) {
        $scrapeParams.Headless = $true
    }
    if ($ShowProgress -or $PSBoundParameters.ContainsKey("Verbose")) {
        $scrapeParams.ShowProgress = $true
    }

    & $scrapeScript @scrapeParams
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }

    git add -- $Path
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }

    git diff --cached --quiet -- $Path
    if ($LASTEXITCODE -eq 0) {
        Write-Host "data/tickets.yml 변경사항이 없습니다."
        return
    }

    git commit -m $CommitMessage
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }

    if ($NoPush) {
        Write-Host "커밋까지만 완료했습니다. -NoPush 옵션으로 원격 푸시는 건너뜁니다."
        return
    }

    git pull --rebase
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }

    git push
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }

    Write-Host "GitHub Pages에서 새 구매번호를 확인할 수 있습니다."
} finally {
    Pop-Location
}
