# 로컬 구매내역 스크래퍼의 텍스트 판별과 파싱을 검증하는 테스트
import unittest

from dhlottery_checker.ledger_scraper import (
    LOGIN_SUBMIT_SELECTORS,
    PASSWORD_SELECTORS,
    USERNAME_SELECTORS,
    _first_visible_locator,
    _is_navigation_interruption,
    _is_ticket_button_candidate,
    _ledger_list_summary,
    _looks_like_ticket_text,
    _parse_env_text,
    _parse_ticket_texts,
    _text_added_after_click,
    load_dhlottery_credentials,
    is_ticket_button_label,
)


class LedgerScraperTest(unittest.TestCase):
    def test_prioritizes_current_dhlottery_login_selectors(self):
        self.assertEqual(PASSWORD_SELECTORS[0], "#inpUserPswdEncn")
        self.assertEqual(USERNAME_SELECTORS[0], "#inpUserId")
        self.assertEqual(LOGIN_SUBMIT_SELECTORS[0], "#btnLogin")

    def test_detects_ticket_view_button_labels(self):
        self.assertTrue(is_ticket_button_label("티켓 보기"))
        self.assertTrue(is_ticket_button_label("상세보기"))
        self.assertTrue(is_ticket_button_label("img alt=복권번호보기"))
        self.assertTrue(is_ticket_button_label("btn-search 로또6/45 (1224) 구입일자 추첨일자"))
        self.assertTrue(is_ticket_button_label("연금복권720+ (315) 1조 052414 구입일자 2026-05-10 추첨일자 2026-05-14"))
        self.assertFalse(is_ticket_button_label("조회"))

    def test_detects_search_icon_with_ticket_row_context(self):
        own = "btn-search ico-search"
        context = "로또6/45\n1224\n68365 78496 66600 43342 43250 50974\n구입일자\n2026-05-10\n추첨일자\n2026-05-16"

        self.assertTrue(_is_ticket_button_candidate(own, context))
        self.assertTrue(_is_ticket_button_candidate("68365 78496 66600 43342 43250 50974 whl-txt barcd", context))
        self.assertFalse(_is_ticket_button_candidate("btn-search", "검색 조건 로또6/45 전체"))

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

    def test_renumbers_lotto_slots_across_multiple_purchase_popups(self):
        imported = _parse_ticket_texts(
            [
                """
로또6/45 티켓 보기
1224회
A 자동
16
23
30
32
35
37
B 자동
7
10
17
18
26
32
C 자동
1
4
14
17
39
41
D 자동
9
13
20
21
36
41
""",
                """
로또6/45 티켓 보기
1224회
A 자동
9
12
13
33
35
43
""",
            ]
        )

        self.assertEqual([ticket.slot for ticket in imported.lotto], ["A", "B", "C", "D", "E"])
        self.assertEqual(imported.lotto[-1].numbers, (9, 12, 13, 33, 35, 43))

    def test_renumbers_pension_slots_across_multiple_purchase_popups(self):
        imported = _parse_ticket_texts(
            [
                """
연금복권720+ 구매번호
315회
1조
0
5
2
4
1
4
""",
                """
연금복권720+ 구매번호
315회
2조
0
5
2
4
1
4
""",
            ]
        )

        self.assertEqual([ticket.slot for ticket in imported.pension], ["1", "2"])
        self.assertEqual([ticket.group for ticket in imported.pension], [1, 2])

    def test_detects_navigation_interruption(self):
        message = (
            'Page.goto: Navigation to "https://www.dhlottery.co.kr/mypage/mylotteryledger" '
            'is interrupted by another navigation to "https://www.dhlottery.co.kr/login/loginSuccess.do?returnUrl=/main"'
        )

        self.assertTrue(_is_navigation_interruption(Exception(message)))
        self.assertFalse(_is_navigation_interruption(Exception("Page.goto: net::ERR_NAME_NOT_RESOLVED")))

    def test_parses_local_env_credentials(self):
        values = _parse_env_text(
            """
            # local only
            DHLOTTERY_ID=sample-user
            DHLOTTERY_PASSWORD="sample-password"
            """
        )

        self.assertEqual(values["DHLOTTERY_ID"], "sample-user")
        self.assertEqual(values["DHLOTTERY_PASSWORD"], "sample-password")

    def test_loads_credentials_from_env_file(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / ".env"
            env_path.write_text("DHLOTTERY_ID=sample-user\nDHLOTTERY_PASSWORD=sample-password\n", encoding="utf-8")

            username, password = load_dhlottery_credentials(env_path)

        self.assertEqual(username, "sample-user")
        self.assertEqual(password, "sample-password")

    def test_first_visible_locator_checks_all_matching_elements(self):
        hidden = _FakeElement(False)
        visible = _FakeElement(True)
        page = _FakePage({"input[type='password']": [hidden, visible]})

        self.assertIs(_first_visible_locator(page, ("input[type='password']",)), visible)

    def test_text_added_after_click_prefers_modal_lines(self):
        before = [
            """
연금복권720+ (315)
1조 052414
구입일자 2026-05-10
추첨일자 2026-05-14
로또6/45 (1224)
68365 78496 66600 43342 43250 50974
구입일자 2026-05-10
추첨일자 2026-05-16
"""
        ]
        after = [
            before[0]
            + """
로또6/45 티켓 보기
1224회
발행일 2026/05/10 (일) 14:55:24
추첨일 2026/05/16
68365 78496 66600 43342 43250 50974
A 자동 16 23 30 32 35 37
B 자동 7 10 17 18 26 32
C 자동 1 4 14 17 39 41
D 자동 9 13 20 21 36 41
합계 4,000원
"""
        ]

        self.assertIn("로또6/45 티켓 보기", _text_added_after_click(before, after))
        self.assertNotIn("연금복권720+ (315)", _text_added_after_click(before, after))

    def test_ledger_list_summary_counts_visible_rows(self):
        summary = _ledger_list_summary(
            [
                """
연금복권720+
315
1조 052414
구입일자
2026-05-10
추첨일자
2026-05-14
로또6/45
1224
68365 78496 66600 43342 43250 50974
구입일자
2026-05-10
추첨일자
2026-05-16
"""
            ]
        )

        self.assertEqual(summary, "구매내역 목록 감지. 로또 1건, 연금복권 1건.")

class _FakePage:
    def __init__(self, elements_by_selector):
        self.frames = [_FakeFrame(elements_by_selector)]


class _FakeFrame:
    def __init__(self, elements_by_selector):
        self._elements_by_selector = elements_by_selector

    def locator(self, selector):
        return _FakeLocator(self._elements_by_selector.get(selector, []))


class _FakeLocator:
    def __init__(self, elements):
        self._elements = elements

    def count(self):
        return len(self._elements)

    def nth(self, index):
        return self._elements[index]


class _FakeElement:
    def __init__(self, visible):
        self._visible = visible

    def is_visible(self, timeout=None):
        return self._visible


if __name__ == "__main__":
    unittest.main()
