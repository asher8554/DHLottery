# 동행복권 구매내역을 가져와 data/tickets.yml을 커밋하고 원격에 올리는 스크립트
[CmdletBinding()]
param(
    [string]$Path = "data/tickets.yml",
    [string]$AccountPath = "data/account.yml",
    [string]$ScraperStatusPath = "data/scraper-status.yml",
    [string]$ScraperSource = "windows",
    [string]$ProfileDir = ".browser/dhlottery",
    [string]$EnvFile = ".env",
    [string]$LoginUrl = "https://www.dhlottery.co.kr/login",
    [string]$MainUrl = "https://www.dhlottery.co.kr/main",
    [int]$MaxTickets = 30,
    [switch]$Append,
    [switch]$Headless,
    [switch]$ShowProgress,
    [switch]$NoPush,
    [string]$CommitMessage = "구매번호 자동 반영"
)

$ErrorActionPreference = "Stop"

try {
    [Console]::InputEncoding = [System.Text.Encoding]::UTF8
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    $OutputEncoding = [System.Text.Encoding]::UTF8
} catch {
    # 오래된 콘솔에서는 인코딩 설정이 실패해도 스크래핑 자체는 계속 진행합니다.
}

$repoRoot = Split-Path -Parent $PSScriptRoot
$scrapeScript = Join-Path $PSScriptRoot "scrape-ledger.ps1"

function Stop-IfNativeFailed {
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}

function Get-ScraperSourceLabel {
    param([string]$Source)

    switch ($Source) {
        "synology" { return "시놀로지 실행" }
        "windows" { return "Windows 실행" }
        "linux" { return "Linux 실행" }
        default { return $Source }
    }
}

function Format-YamlScalar {
    param([string]$Value)

    return '"' + ($Value -replace '"', '\"') + '"'
}

function Write-ScraperStatus {
    param(
        [string]$Path,
        [string]$Source
    )

    $statusDir = Split-Path -Parent $Path
    if ($statusDir) {
        New-Item -ItemType Directory -Force -Path $statusDir | Out-Null
    }

    $updatedAt = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ", [System.Globalization.CultureInfo]::InvariantCulture)
    $sourceLabel = Get-ScraperSourceLabel -Source $Source
    $content = @(
        "source: $(Format-YamlScalar -Value $Source)",
        "source_label: $(Format-YamlScalar -Value $sourceLabel)",
        "updated_at: $(Format-YamlScalar -Value $updatedAt)"
    )
    Set-Content -LiteralPath $Path -Value $content -Encoding UTF8
}

Push-Location $repoRoot
try {
    $scrapeParams = @{
        Path = $Path
        AccountPath = $AccountPath
        ProfileDir = $ProfileDir
        EnvFile = $EnvFile
        LoginUrl = $LoginUrl
        MainUrl = $MainUrl
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
    Stop-IfNativeFailed
    Write-ScraperStatus -Path $ScraperStatusPath -Source $ScraperSource

    $changePaths = @($Path)
    if ($AccountPath) {
        $changePaths += $AccountPath
    }
    if ($ScraperStatusPath) {
        $changePaths += $ScraperStatusPath
    }

    git add -- $changePaths
    Stop-IfNativeFailed

    git diff --cached --quiet -- $changePaths
    $diffExitCode = $LASTEXITCODE
    if ($diffExitCode -eq 0) {
        Write-Host "구매번호와 예치금 변경사항이 없습니다."
        return
    }
    if ($diffExitCode -ne 1) {
        exit $diffExitCode
    }

    git commit -m $CommitMessage
    Stop-IfNativeFailed

    if ($NoPush) {
        Write-Host "커밋까지만 완료했습니다. -NoPush 옵션으로 원격 푸시는 건너뜁니다."
        return
    }

    git pull --rebase
    Stop-IfNativeFailed

    git push
    Stop-IfNativeFailed

    Write-Host "GitHub Pages에서 새 구매번호를 확인할 수 있습니다."
} finally {
    Pop-Location
}
