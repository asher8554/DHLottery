# 연금복권 등수 계산을 검증하는 테스트
import unittest

from dhlottery_checker.pension import PensionWinning, check_pension


class PensionMatchTest(unittest.TestCase):
    def setUp(self):
        self.winning = PensionWinning(
            round=314,
            draw_date="2026-05-07",
            group=2,
            number="060727",
            bonus_number="293160",
        )

    def test_first_rank(self):
        matches = check_pension(2, "060727", self.winning)
        self.assertEqual(matches[0].rank_label, "1등")

    def test_second_rank(self):
        matches = check_pension(1, "060727", self.winning)
        self.assertEqual(matches[0].rank_label, "2등")

    def test_suffix_rank(self):
        matches = check_pension(4, "990727", self.winning)
        self.assertEqual(matches[0].rank_label, "4등")

    def test_bonus(self):
        matches = check_pension(5, "293160", self.winning)
        self.assertEqual(matches[0].rank_label, "보너스")

    def test_bonus_takes_precedence_over_lower_suffix_rank(self):
        winning = PensionWinning(
            round=314,
            draw_date="2026-05-07",
            group=2,
            number="060727",
            bonus_number="293127",
        )

        matches = check_pension(5, "293127", winning)

        self.assertEqual([match.rank_label for match in matches], ["보너스"])

    def test_rejects_invalid_selected_group(self):
        with self.assertRaisesRegex(ValueError, "group"):
            check_pension(0, "293160", self.winning)

    def test_rejects_invalid_selected_number(self):
        with self.assertRaisesRegex(ValueError, "number"):
            check_pension(5, "29316", self.winning)


if __name__ == "__main__":
    unittest.main()
