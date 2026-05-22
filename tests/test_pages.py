# Pages 정적 HTML의 주요 UI 계약을 검증하는 테스트
from pathlib import Path
import unittest


class PagesHtmlTest(unittest.TestCase):
    def test_ticket_entry_renders_result_history_details(self):
        html = Path("docs/ticket-entry.html").read_text(encoding="utf-8")

        self.assertIn("history-card", html)
        self.assertIn("function historyWinningText", html)
        self.assertIn("function appendHistoryTicketBadge", html)
        self.assertIn("entry.winning", html)
        self.assertIn("entry.tickets", html)


if __name__ == "__main__":
    unittest.main()
