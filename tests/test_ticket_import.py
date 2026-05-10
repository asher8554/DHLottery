# 동행복권 티켓 보기 텍스트 가져오기를 검증하는 테스트
from pathlib import Path
import tempfile
import unittest

from dhlottery_checker.config import load_ticket_config
from dhlottery_checker.ticket_import import parse_lotto_ticket_text, write_lotto_tickets


class TicketImportTest(unittest.TestCase):
    def test_parses_simple_lotto_numbers(self):
        text = """
1224회
9

12

13

33

35

43
"""

        tickets = parse_lotto_ticket_text(text)

        self.assertEqual(tickets[0].round, 1224)
        self.assertEqual(tickets[0].slot, "A")
        self.assertEqual(tickets[0].numbers, (9, 12, 13, 33, 35, 43))

    def test_parses_lotto_ticket_view_text(self):
        text = """
로또6/45 티켓 보기
1224회
발행일 2026/05/10 (일) 12:55:42
추첨일 2026/05/16
64315 53510 57779 62575 50796 26908
A 자동
9 12 13 33 35 43
합계 1,000원
"""

        tickets = parse_lotto_ticket_text(text)

        self.assertEqual(tickets[0].round, 1224)
        self.assertEqual(tickets[0].slot, "A")
        self.assertEqual(tickets[0].numbers, (9, 12, 13, 33, 35, 43))

    def test_rejects_identifier_numbers_without_selected_row(self):
        text = """
2026-05-10
로또6/45
1224
64315 53510 57779 62575 50796 26908
1
미추첨
-
2026-05-16
미해당
"""

        with self.assertRaises(ValueError):
            parse_lotto_ticket_text(text)

    def test_writes_lotto_tickets_and_preserves_pension(self):
        text = """
로또6/45 티켓 보기
1224회
A 자동 9 12 13 33 35 43
"""
        tickets = parse_lotto_ticket_text(text)

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "tickets.yml"
            path.write_text(
                """
pension:
  tickets:
    - label: "연금복권 예시"
      round: 314
      group: 2
      number: "060727"
""",
                encoding="utf-8",
            )

            write_lotto_tickets(path, tickets, replace_lotto=True)
            config = load_ticket_config(path)

        self.assertEqual(config.lotto[0].round, 1224)
        self.assertEqual(config.lotto[0].numbers, (9, 12, 13, 33, 35, 43))
        self.assertEqual(config.pension[0].number, "060727")

    def test_replace_all_removes_existing_pension(self):
        text = """
로또6/45 티켓 보기
1224회
A 자동 9 12 13 33 35 43
"""
        tickets = parse_lotto_ticket_text(text)

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "tickets.yml"
            path.write_text(
                """
pension:
  tickets:
    - label: "연금복권 예시"
      round: 314
      group: 2
      number: "060727"
""",
                encoding="utf-8",
            )

            write_lotto_tickets(path, tickets, replace_all=True)
            config = load_ticket_config(path)

        self.assertEqual(config.lotto[0].round, 1224)
        self.assertEqual(config.pension, ())


if __name__ == "__main__":
    unittest.main()
