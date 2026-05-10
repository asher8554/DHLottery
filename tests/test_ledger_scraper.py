# 로컬 구매내역 스크래퍼의 텍스트 판별과 파싱을 검증하는 테스트
import unittest

from dhlottery_checker.ledger_scraper import (
    _is_navigation_interruption,
    _looks_like_ticket_text,
    _parse_ticket_texts,
    is_ticket_button_label,
)


class LedgerScraperTest(unittest.TestCase):
    def test_detects_ticket_view_button_labels(self):
        self.assertTrue(is_ticket_button_label("티켓 보기"))
        self.assertTrue(is_ticket_button_label("상세보기"))
        self.assertFalse(is_ticket_button_label("조회"))

    def test_detects_ticket_text(self):
        self.assertTrue(_looks_like_ticket_text("로또6/45 티켓 보기\n1224회\nA 자동 9 12 13 33 35 43"))
        self.assertTrue(_looks_like_ticket_text("연금복권720+\n315회\n1조\n0\n5\n2\n4\n1\n4"))
        self.assertFalse(_looks_like_ticket_text("구매/당첨내역 조회 결과"))

    def test_parses_mixed_ticket_texts(self):
        imported = _parse_ticket_texts(
            [
                "로또6/45 티켓 보기\n1224회\nA 자동 9 12 13 33 35 43",
                "연금복권720+\n315회\n1조\n0\n5\n2\n4\n1\n4",
            ]
        )

        self.assertEqual(len(imported.lotto), 1)
        self.assertEqual(imported.lotto[0].numbers, (9, 12, 13, 33, 35, 43))
        self.assertEqual(len(imported.pension), 1)
        self.assertEqual(imported.pension[0].number, "052414")

    def test_detects_navigation_interruption(self):
        message = (
            'Page.goto: Navigation to "https://www.dhlottery.co.kr/mypage/mylotteryledger" '
            'is interrupted by another navigation to "https://www.dhlottery.co.kr/login/loginSuccess.do?returnUrl=/main"'
        )

        self.assertTrue(_is_navigation_interruption(Exception(message)))
        self.assertFalse(_is_navigation_interruption(Exception("Page.goto: net::ERR_NAME_NOT_RESOLVED")))


if __name__ == "__main__":
    unittest.main()
