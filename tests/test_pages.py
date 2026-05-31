# Pages 정적 HTML의 주요 UI 계약을 검증하는 테스트
from pathlib import Path
import unittest


class PagesHtmlTest(unittest.TestCase):
    def test_ticket_entry_links_to_dhlottery_home(self):
        html = Path("docs/ticket-entry.html").read_text(encoding="utf-8")

        self.assertIn("동행복권 바로가기", html)
        self.assertIn('href="https://www.dhlottery.co.kr/"', html)

    def test_ticket_entry_renders_result_history_details(self):
        html = Path("docs/ticket-entry.html").read_text(encoding="utf-8")

        self.assertIn("history-card", html)
        self.assertIn("function historyWinningText", html)
        self.assertIn("function appendHistoryTicketBadge", html)
        self.assertIn("entry.winning", html)
        self.assertIn("entry.tickets", html)

    def test_ticket_entry_separates_history_ticket_number_from_result(self):
        html = Path("docs/ticket-entry.html").read_text(encoding="utf-8")

        self.assertIn("history-ticket-number", html)
        self.assertIn("history-ticket-result", html)
        self.assertIn("appendHistoryTicketBadge(tickets, entry, ticket, index)", html)

    def test_history_ticket_badges_include_short_game_label(self):
        html = Path("docs/ticket-entry.html").read_text(encoding="utf-8")

        self.assertIn("function historyTicketBadgeLabel(entry, ticket, index)", html)
        self.assertIn('if (entry.game === "pension")', html)
        self.assertIn('return `연금 ${ticketNumberText}`;', html)
        self.assertIn('if (entry.game === "lotto")', html)
        self.assertIn('return `로또 ${ticketNumberText}`;', html)
        self.assertIn("appendHistoryTicketBadge(tickets, entry, ticket, index)", html)

    def test_history_ticket_badges_use_default_wrapping_layout(self):
        html = Path("docs/ticket-entry.html").read_text(encoding="utf-8")

        self.assertIn(".history-ticket-list {\n      display: flex;\n      flex-wrap: wrap;\n      gap: 6px;\n    }", html)
        self.assertIn('tickets.className = "history-ticket-list";', html)
        self.assertNotIn("five-up", html)

    def test_output_panel_uses_original_two_column_layout(self):
        html = Path("docs/ticket-entry.html").read_text(encoding="utf-8")

        self.assertIn('<section class="panel" aria-labelledby="output-title">', html)
        self.assertIn("grid-template-columns: minmax(0, 0.74fr) minmax(380px, 1fr);", html)
        self.assertIn("width: min(1120px, calc(100% - 32px));", html)
        self.assertIn("@media (max-width: 860px)", html)
        self.assertNotIn("output-panel", html)

    def test_ticket_summary_splits_lotto_and_pension_columns(self):
        html = Path("docs/ticket-entry.html").read_text(encoding="utf-8")

        self.assertIn(".ticket-summary.split", html)
        self.assertIn(".ticket-column", html)
        self.assertIn("function createTicketColumn", html)
        self.assertIn('ticketSummary.className = shouldSplit ? "ticket-summary split" : "ticket-summary";', html)
        self.assertIn("appendTicketRow(lottoColumn", html)
        self.assertIn("appendTicketRow(pensionColumn", html)

    def test_result_history_splits_lotto_and_pension_columns(self):
        html = Path("docs/ticket-entry.html").read_text(encoding="utf-8")

        self.assertIn(".history-list.split", html)
        self.assertIn(".history-column", html)
        self.assertIn("function appendHistoryColumn", html)
        self.assertIn('resultHistoryList.className = shouldSplit ? "history-list split" : "history-list";', html)
        self.assertIn('appendHistoryColumn("lotto"', html)
        self.assertIn('appendHistoryColumn("pension"', html)

    def test_result_history_shows_latest_completed_entries(self):
        html = Path("docs/ticket-entry.html").read_text(encoding="utf-8")

        self.assertIn("<summary>최근 당첨결과", html)
        self.assertIn('aria-label="최근 당첨결과"', html)
        self.assertIn("function latestResultHistoryEntries(entries)", html)
        self.assertIn("const visibleEntries = latestResultHistoryEntries(entries).slice(0, 20);", html)
        self.assertIn("아직 저장된 최근 당첨결과가 없습니다.", html)

    def test_result_history_uses_smaller_text_scale(self):
        html = Path("docs/ticket-entry.html").read_text(encoding="utf-8")

        self.assertIn(".history-summary {\n      color: var(--text);\n      font-size: 13px;", html)
        self.assertIn(".history-winning {\n      color: var(--muted);\n      font-size: 12px;", html)
        self.assertIn(".history-ticket {\n      display: inline-grid;\n      grid-template-columns: auto auto;\n      align-items: stretch;\n      min-height: 28px;\n      border: 1px solid var(--line);\n      border-radius: 8px;\n      background: var(--surface);\n      color: var(--muted);\n      font-size: 12px;", html)

    def test_mobile_layout_uses_compact_controls_and_results(self):
        html = Path("docs/ticket-entry.html").read_text(encoding="utf-8")

        self.assertIn("@media (max-width: 440px)", html)
        self.assertIn(".top-actions {\n        display: grid;\n        grid-template-columns: 1fr 1fr;\n        width: 100%;", html)
        self.assertIn(".top-actions .external-button {\n        grid-column: 1 / -1;\n        width: 100%;", html)
        self.assertIn(".panel-body {\n        gap: 12px;\n        padding: 14px;", html)
        self.assertIn(".stat-row {\n        min-height: 34px;\n        padding: 7px 9px;", html)
        self.assertIn(".ticket-summary.split {\n        grid-template-columns: repeat(2, minmax(0, 1fr));", html)
        self.assertIn(".ticket-row {\n        align-items: start;\n        grid-template-columns: 1fr;\n        gap: 4px;\n        font-size: 12px;", html)

    def test_ticket_entry_shows_money_summary_stats(self):
        html = Path("docs/ticket-entry.html").read_text(encoding="utf-8")

        self.assertIn('<span class="stat-label">누적 당첨금액</span>', html)
        self.assertIn('class="stat-value money-prize" id="totalPrizeAmount"', html)
        self.assertIn('<span class="stat-label">누적 복권금액</span>', html)
        self.assertIn('class="stat-value money-cost" id="totalTicketCost"', html)

    def test_ticket_entry_uses_distinct_money_summary_colors(self):
        html = Path("docs/ticket-entry.html").read_text(encoding="utf-8")

        self.assertIn("--money-prize: var(--good);", html)
        self.assertIn("--money-cost: #9a6700;", html)
        self.assertIn("--money-cost: #f4c95d;", html)
        self.assertIn(".stat-value.money-prize {\n      color: var(--money-prize);", html)
        self.assertIn(".stat-value.money-cost {\n      color: var(--money-cost);", html)

    def test_low_balance_status_blinks(self):
        html = Path("docs/ticket-entry.html").read_text(encoding="utf-8")

        self.assertIn("@keyframes balance-alert-blink", html)
        self.assertIn(".stat-value.balance-low", html)
        self.assertIn("animation: balance-alert-blink 0.8s steps(2, start) infinite;", html)
        self.assertIn("@media (prefers-reduced-motion: reduce)", html)
        self.assertIn('balanceStatus.classList.toggle("balance-low", isLowBalance);', html)
        self.assertIn('balanceStatus.classList.toggle("balance-ok", !isLowBalance);', html)

    def test_ticket_entry_calculates_money_summary_from_history_and_tickets(self):
        html = Path("docs/ticket-entry.html").read_text(encoding="utf-8")

        self.assertIn("const ticketPriceKrw = 1000;", html)
        self.assertIn("const totalPrizeAmount = document.querySelector(\"#totalPrizeAmount\");", html)
        self.assertIn("const totalTicketCost = document.querySelector(\"#totalTicketCost\");", html)
        self.assertIn("current.prizes = [];", html)
        self.assertIn("function parsePrizeAmountKrw", html)
        self.assertIn("function totalPrizeAmountKrw", html)
        self.assertIn("function totalTicketCostKrw", html)
        self.assertIn("function renderMoneySummary", html)
        self.assertIn("amountText.includes(\"월\")", html)
        self.assertIn("ticketPriceKrw", html)

    def test_ticket_entry_surfaces_scraper_run_status(self):
        html = Path("docs/ticket-entry.html").read_text(encoding="utf-8")

        self.assertIn('id="scraperRunStatus"', html)
        self.assertIn("function renderScraperRunStatus", html)
        self.assertIn("scraper-status good", html)
        self.assertIn("bash scripts/synology-docker-run.sh", html)
        self.assertIn(".\\scripts\\scrape-ledger-and-push.ps1 -ShowProgress", html)

    def test_ticket_entry_does_not_warn_for_old_scraper_timestamp(self):
        html = Path("docs/ticket-entry.html").read_text(encoding="utf-8")

        self.assertNotIn("staleMs", html)
        self.assertNotIn("확인 필요", html)
        self.assertNotIn("scraper-status bad", html)

    def test_ticket_entry_loads_scraper_status_metadata(self):
        html = Path("docs/ticket-entry.html").read_text(encoding="utf-8")

        self.assertIn("const scraperStatusApiUrl", html)
        self.assertIn("const scraperStatusRawUrl", html)
        self.assertIn("data/scraper-status.yml", html)
        self.assertIn("function decodeBase64Utf8", html)
        self.assertIn("function loadScraperStatusYaml", html)
        self.assertIn("api.github.com/repos/asher8554/DHLottery/contents/data/scraper-status.yml", html)
        self.assertIn("function parseScraperStatusYaml", html)
        self.assertIn("function scraperSourceLabel", html)
        self.assertIn("function loadScraperStatus", html)
        self.assertIn("currentAccountUpdatedAt", html)
        self.assertIn("시놀로지 실행", html)

    def test_scraper_push_scripts_record_execution_source(self):
        bash = Path("scripts/scrape-ledger-and-push.sh").read_text(encoding="utf-8")
        synology = Path("scripts/synology-docker-run.sh").read_text(encoding="utf-8")
        powershell = Path("scripts/scrape-ledger-and-push.ps1").read_text(encoding="utf-8")

        self.assertIn('status_path="${SCRAPER_STATUS_PATH:-data/scraper-status.yml}"', bash)
        self.assertIn('scraper_source="${SCRAPER_SOURCE:-linux}"', bash)
        self.assertIn("write_scraper_status", bash)
        self.assertIn('"SCRAPER_SOURCE=${SCRAPER_SOURCE:-synology}"', synology)
        self.assertIn("SCRAPER_STATUS_PATH", synology)
        self.assertIn('[string]$ScraperStatusPath = "data/scraper-status.yml"', powershell)
        self.assertIn('[string]$ScraperSource = "windows"', powershell)
        self.assertIn("Write-ScraperStatus", powershell)

    def test_scraper_push_scripts_prune_completed_history_rounds(self):
        bash = Path("scripts/scrape-ledger-and-push.sh").read_text(encoding="utf-8")
        powershell = Path("scripts/scrape-ledger-and-push.ps1").read_text(encoding="utf-8")

        self.assertIn(
            'prune-sent-tickets --tickets "$ticket_path" --status-json .state/check-status.json --history data/result-history.yml',
            bash,
        )
        self.assertIn("prune-sent-tickets", powershell)
        self.assertIn("--history", powershell)
        self.assertIn("data/result-history.yml", powershell)

    def test_synology_push_script_checks_git_state_before_scraping(self):
        bash = Path("scripts/scrape-ledger-and-push.sh").read_text(encoding="utf-8")

        self.assertIn('target_branch="${TARGET_BRANCH:-main}"', bash)
        self.assertIn("ensure_git_ready", bash)
        self.assertIn("rebase-merge", bash)
        self.assertIn("git branch --show-current", bash)
        self.assertIn('git checkout "$target_branch"', bash)
        self.assertIn('git checkout -b "$target_branch" "origin/$target_branch"', bash)
        self.assertIn('git pull --rebase origin "$target_branch"', bash)
        self.assertIn('git push origin "$target_branch"', bash)
        self.assertLess(
            bash.index("ensure_git_ready"),
            bash.index('bash "$repo_root/scripts/scrape-ledger.sh"'),
        )


if __name__ == "__main__":
    unittest.main()
