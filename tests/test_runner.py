# 검사 실행기의 중복 알림 처리 옵션을 검증하는 테스트
from __future__ import annotations

import argparse
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from dhlottery_checker.config import LottoTicket
from dhlottery_checker.http import HttpError
from dhlottery_checker.runner import Outcome, _format_messages, _run_check


class RunnerTest(unittest.TestCase):
    def test_force_notify_sends_previously_sent_outcome(self):
        outcome = Outcome("lotto", 1223, "로또 1223회 A", "재전송 결과", "same-ticket", True)

        with patch("dhlottery_checker.runner.load_ticket_config", return_value=SimpleNamespace(lotto=[], pension=[])):
            with patch("dhlottery_checker.runner._build_outcomes", return_value=[outcome]):
                with patch("dhlottery_checker.runner.send_kakao_text") as send_kakao:
                    with patch("builtins.print"):
                        with self.subTest("normal duplicate is skipped"):
                            args = self._args(force_notify=False)
                            _run_check(args)
                            _run_check(args)
                            send_kakao.reset_mock()
                            _run_check(args)
                            send_kakao.assert_not_called()

                        with self.subTest("force duplicate is resent and state remains usable"):
                            args = self._args(force_notify=True)
                            _run_check(args)
                            self.assertEqual(send_kakao.call_count, 2)
                            sent_text = "\n\n".join(call.args[0] for call in send_kakao.call_args_list)
                            self.assertIn("[동행복권 결과 요약]", sent_text)
                            self.assertIn("동행복권 결과 상세", sent_text)
                            self.assertIn("재전송 결과", sent_text)

    def test_formats_summary_and_detail_messages(self):
        messages = _format_messages(
            [
                Outcome(
                    "lotto",
                    1223,
                    "로또 1223회 A",
                    "로또 1223회 A. 5등 5,000원.",
                    "ticket-a",
                    True,
                    won=True,
                    result_label="5등 5,000원",
                    match_count=3,
                    summary_text="A 5등 5,000원",
                    detail_header="로또 1223회 당첨번호 16, 18, 20, 32, 33, 39 + 26",
                    detail_text="A. 5등 5,000원. 맞은 번호 16, 18, 20.",
                ),
                Outcome(
                    "lotto",
                    1223,
                    "로또 1223회 B",
                    "로또 1223회 B. 미당첨.",
                    "ticket-b",
                    True,
                    won=False,
                    result_label="미당첨",
                    match_count=2,
                    summary_text="B 미당첨",
                    detail_header="로또 1223회 당첨번호 16, 18, 20, 32, 33, 39 + 26",
                    detail_text="B. 미당첨. 맞은 번호 18, 32. 보너스 일치.",
                ),
            ],
            [],
        )

        self.assertEqual(len(messages), 2)
        self.assertIn("[동행복권 결과 요약]", messages[0])
        self.assertIn("로또 1223회. 당첨 1개, 미당첨 1개.", messages[0])
        self.assertIn("당첨. A 5등 5,000원.", messages[0])
        self.assertIn("로또 1223회 https://www.dhlottery.co.kr/lt645/result", messages[0])
        self.assertIn("로또는 3개부터 당첨입니다.", messages[1])
        self.assertIn("B. 미당첨. 맞은 번호 18, 32. 보너스 일치.", messages[1])

    def test_formats_pension_winner_in_summary(self):
        messages = _format_messages(
            [
                Outcome(
                    "pension",
                    314,
                    "연금복권 314회 1",
                    "연금복권 314회 1. 1등 월 700만원 x 20년.",
                    "pension-ticket",
                    True,
                    won=True,
                    result_label="1등 월 700만원 x 20년",
                    summary_text="1 2조 060727 1등 월 700만원 x 20년",
                    detail_header="연금복권 314회 당첨번호 2조 060727, 보너스 각조 293160",
                    detail_text="1. 1등 월 700만원 x 20년. 내 번호 2조 060727.",
                )
            ],
            [],
        )

        self.assertIn("연금복권 314회. 당첨 1개, 미당첨 0개.", messages[0])
        self.assertIn("당첨. 1 2조 060727 1등 월 700만원 x 20년.", messages[0])
        self.assertIn("연금복권 314회 https://www.dhlottery.co.kr/pt720/result", messages[0])

    def test_formats_no_winner_summary_in_requested_style(self):
        messages = _format_messages(
            [
                Outcome("lotto", 1223, "로또 1223회 A", "A. 미당첨.", "lotto-a", True, match_count=2),
                Outcome("lotto", 1223, "로또 1223회 B", "B. 미당첨.", "lotto-b", True, match_count=1),
                Outcome("pension", 314, "연금복권 314회 1", "1. 미당첨.", "pension-1", True),
            ],
            [],
        )

        self.assertEqual(
            messages[0],
            "\n".join(
                [
                    "[동행복권 결과 요약]",
                    "로또 1223회. 당첨 0개, 미당첨 2개.",
                    "연금복권 314회. 당첨 0개, 미당첨 1개.",
                    "이번 회차는 당첨 없음.",
                    "결과 확인",
                    "로또 1223회 https://www.dhlottery.co.kr/lt645/result",
                    "연금복권 314회 https://www.dhlottery.co.kr/pt720/result",
                ]
            ),
        )
        self.assertNotIn("최고 일치", messages[0])

    def test_lottery_http_error_does_not_fail_run(self):
        config = SimpleNamespace(
            lotto=(LottoTicket(round=1224, numbers=(9, 12, 13, 33, 35, 43), label="로또 1224회 A"),),
            pension=(),
        )

        with patch("dhlottery_checker.runner.load_ticket_config", return_value=config):
            with patch("dhlottery_checker.runner.fetch_lotto_winning", side_effect=HttpError("timeout")):
                with patch("dhlottery_checker.runner.send_kakao_text") as send_kakao:
                    with patch("builtins.print") as print_mock:
                        result = _run_check(self._args(force_notify=False))

        self.assertEqual(result, 0)
        send_kakao.assert_not_called()
        output = "\n".join(call.args[0] for call in print_mock.call_args_list)
        self.assertIn("결과 조회 실패", output)
        self.assertIn("다음 실행에서 다시 시도합니다", output)

    def _args(self, force_notify: bool) -> argparse.Namespace:
        return argparse.Namespace(
            tickets="unused.yml",
            game="all",
            notify=True,
            dry_run=False,
            state=str(self.state_path),
            no_state=False,
            force_notify=force_notify,
        )

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.state_path = Path(self.temp_dir.name) / "sent-results.json"

    def tearDown(self):
        self.temp_dir.cleanup()


if __name__ == "__main__":
    unittest.main()
