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

    def test_history_ticket_badges_fit_five_items_on_desktop(self):
        html = Path("docs/ticket-entry.html").read_text(encoding="utf-8")

        self.assertIn(".history-ticket-list.five-up", html)
        self.assertIn("grid-template-columns: repeat(5, max-content);", html)
        self.assertIn('tickets.className = entry.tickets.length === 5 ? "history-ticket-list five-up" : "history-ticket-list";', html)
        self.assertIn("justify-content: start;", html)
        self.assertIn("@media (max-width: 720px)", html)

    def test_output_panel_gets_more_horizontal_space(self):
        html = Path("docs/ticket-entry.html").read_text(encoding="utf-8")

        self.assertIn('class="panel output-panel"', html)
        self.assertIn(".output-panel {", html)
        self.assertIn("grid-column: 1 / -1;", html)
        self.assertIn("width: min(1360px, calc(100% - 24px));", html)

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
