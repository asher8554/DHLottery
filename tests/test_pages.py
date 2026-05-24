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
        self.assertIn("appendHistoryTicketBadge(tickets, ticket, index)", html)

    def test_ticket_entry_surfaces_scraper_run_status(self):
        html = Path("docs/ticket-entry.html").read_text(encoding="utf-8")

        self.assertIn('id="scraperRunStatus"', html)
        self.assertIn("function renderScraperRunStatus", html)
        self.assertIn("scraper-status good", html)
        self.assertIn("bash scripts/synology-docker-run.sh", html)
        self.assertIn(".\\scripts\\scrape-ledger-and-push.ps1 -ShowProgress", html)


if __name__ == "__main__":
    unittest.main()
