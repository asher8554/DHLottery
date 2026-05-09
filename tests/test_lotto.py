# 로또 등수 계산을 검증하는 테스트
import unittest

from dhlottery_checker.lotto import LottoWinning, check_lotto


class LottoMatchTest(unittest.TestCase):
    def setUp(self):
        self.winning = LottoWinning(
            round=1222,
            draw_date="2026-05-02",
            numbers=(4, 11, 17, 22, 32, 41),
            bonus=34,
            prize_by_rank={1: 100, 2: 50, 3: 30, 4: 5, 5: 1},
        )

    def test_first_rank(self):
        match = check_lotto((4, 11, 17, 22, 32, 41), self.winning)
        self.assertEqual(match.rank, 1)
        self.assertEqual(match.amount, 100)

    def test_second_rank(self):
        match = check_lotto((4, 11, 17, 22, 32, 34), self.winning)
        self.assertEqual(match.rank, 2)

    def test_no_prize(self):
        match = check_lotto((1, 2, 3, 5, 6, 7), self.winning)
        self.assertIsNone(match.rank)


if __name__ == "__main__":
    unittest.main()

