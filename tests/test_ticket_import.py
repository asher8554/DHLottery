# 동행복권 티켓 보기 텍스트 가져오기를 검증하는 테스트
from pathlib import Path
import tempfile
import unittest

from dhlottery_checker.config import load_ticket_config
from dhlottery_checker.ticket_import import (
    parse_lotto_ticket_text,
    parse_pension_ticket_text,
    parse_ticket_text,
    write_imported_tickets,
    write_lotto_tickets,
)


class TicketImportTest(unittest.TestCase):
    def test_parses_full_ticket_text_with_split_game_blocks(self):
        text = """
1224회
발행일
2026/05/10 (일) 14:55:24
추첨일
2026/05/16
지급기한
2027/05/17
68365
78496
66600
43342
43250
50974
A
자동
16

23

30

32

35

37

B
자동
7

10

17

18

26

32

C
자동
1

4

14

17

39

41

D
자동
9

13

20

21

36

41
E
자동
9

12

13

33

35

43
"""

        tickets = parse_lotto_ticket_text(text)

        self.assertEqual([ticket.slot for ticket in tickets], ["A", "B", "C", "D", "E"])
        self.assertEqual(tickets[0].round, 1224)
        self.assertEqual(tickets[0].numbers, (16, 23, 30, 32, 35, 37))
        self.assertEqual(tickets[1].numbers, (7, 10, 17, 18, 26, 32))
        self.assertEqual(tickets[2].numbers, (1, 4, 14, 17, 39, 41))
        self.assertEqual(tickets[3].numbers, (9, 13, 20, 21, 36, 41))
        self.assertEqual(tickets[4].numbers, (9, 12, 13, 33, 35, 43))

    def test_parses_plain_round_and_numbers(self):
        text = """
1224
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

    def test_parses_plain_round_with_utf8_bom(self):
        text = "\ufeff1224\n9\n12\n13\n33\n35\n43\n"

        tickets = parse_lotto_ticket_text(text)

        self.assertEqual(tickets[0].round, 1224)
        self.assertEqual(tickets[0].numbers, (9, 12, 13, 33, 35, 43))

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

    def test_parses_lotto_ticket_view_text_with_four_games(self):
        text = """
로또6/45 티켓 보기
1224회
발행일 2026/05/10 (일) 14:55:24
추첨일 2026/05/16
지급기한 2027/05/17
68365 78496 66600 43342 43250 50974
A 자동 16 23 30 32 35 37
B 자동 7 10 17 18 26 32
C 자동 1 4 14 17 39 41
D 자동 9 13 20 21 36 41
합계 4,000원
"""

        tickets = parse_lotto_ticket_text(text)

        self.assertEqual([ticket.slot for ticket in tickets], ["A", "B", "C", "D"])
        self.assertEqual(tickets[0].round, 1224)
        self.assertEqual(tickets[3].numbers, (9, 13, 20, 21, 36, 41))

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

    def test_parses_pension_ticket_text_with_noisy_digit(self):
        text = """
315회
발행일
2026/05/10 일요일 14:56:34
추첨일
2026/05/14
지급기한
2027/05/14
1조
0

5

2

4

1

4wj

2조
0

5

2

4

1

4
"""

        tickets = parse_pension_ticket_text(text)

        self.assertEqual(len(tickets), 2)
        self.assertEqual(tickets[0].round, 315)
        self.assertEqual(tickets[0].group, 1)
        self.assertEqual(tickets[0].number, "052414")
        self.assertEqual(tickets[1].group, 2)
        self.assertEqual(tickets[1].number, "052414")

    def test_writes_combined_imported_tickets(self):
        text = """
1224회
A 자동 16 23 30 32 35 37
연금복권720+
315회
1조
0
5
2
4
1
4
"""
        tickets = parse_ticket_text(text)

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "tickets.yml"
            write_imported_tickets(path, tickets, replace_all=True)
            config = load_ticket_config(path)

        self.assertEqual(config.lotto[0].round, 1224)
        self.assertEqual(config.lotto[0].numbers, (16, 23, 30, 32, 35, 37))
        self.assertEqual(config.pension[0].round, 315)
        self.assertEqual(config.pension[0].group, 1)
        self.assertEqual(config.pension[0].number, "052414")


if __name__ == "__main__":
    unittest.main()
