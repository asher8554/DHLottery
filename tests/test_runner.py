# 검사 실행기의 중복 알림 처리 옵션을 검증하는 테스트
from __future__ import annotations

import argparse
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import yaml

from dhlottery_checker.config import LottoTicket
from dhlottery_checker.http import HttpError, HttpTimeoutError
from dhlottery_checker.runner import (
    Outcome,
    _format_messages,
    _run_balance_alert,
    _run_check,
    prune_sent_tickets,
    write_result_history,
)
from dhlottery_checker.state import fingerprint_ticket


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
        self.assertLess(messages[0].index("로또 1223회. 당첨 1개"), messages[0].index("당첨. A 5등"))
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
                    "",
                    "로또 1223회 https://www.dhlottery.co.kr/lt645/result",
                    "연금복권 314회 https://www.dhlottery.co.kr/pt720/result",
                ]
            ),
        )
        self.assertNotIn("최고 일치", messages[0])
        self.assertNotIn("이번 회차는 당첨 없음", messages[0])
        self.assertNotIn("결과 확인", messages[0])

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
        self.assertNotIn("아직 당첨결과 발표 전입니다", output)

    def test_pending_result_message_is_notified_when_enabled(self):
        outcome = Outcome(
            "lotto",
            1224,
            "로또 1224회 A",
            "로또 1224회 A. 결과 대기 중입니다.",
            "pending-ticket",
            False,
        )

        with patch("dhlottery_checker.runner.load_ticket_config", return_value=SimpleNamespace(lotto=[], pension=[])):
            with patch("dhlottery_checker.runner._build_outcomes", return_value=[outcome]):
                with patch("dhlottery_checker.runner.send_kakao_text") as send_kakao:
                    with patch("builtins.print") as print_mock:
                        result = _run_check(self._args(force_notify=False, notify_pending=True))

        self.assertEqual(result, 0)
        send_kakao.assert_called_once()
        message = send_kakao.call_args.args[0]
        self.assertIn("로또 1224회. 아직 당첨결과 발표 전입니다.", message)
        self.assertIn("로또 1224회 https://www.dhlottery.co.kr/lt645/result", message)
        self.assertIn("발표 후 다시 검사하면 당첨 여부를 알려드립니다.", message)
        output = "\n".join(call.args[0] for call in print_mock.call_args_list)
        self.assertIn("아직 당첨결과 발표 전입니다", output)

    def test_pending_result_message_is_not_notified_by_default(self):
        outcome = Outcome(
            "lotto",
            1224,
            "로또 1224회 A",
            "로또 1224회 A. 결과 대기 중입니다.",
            "pending-ticket",
            False,
        )

        with patch("dhlottery_checker.runner.load_ticket_config", return_value=SimpleNamespace(lotto=[], pension=[])):
            with patch("dhlottery_checker.runner._build_outcomes", return_value=[outcome]):
                with patch("dhlottery_checker.runner.send_kakao_text") as send_kakao:
                    with patch("builtins.print") as print_mock:
                        result = _run_check(self._args(force_notify=False))

        self.assertEqual(result, 0)
        send_kakao.assert_not_called()
        output = "\n".join(call.args[0] for call in print_mock.call_args_list)
        self.assertIn("아직 당첨결과 발표 전입니다", output)

    def test_timeout_result_message_is_notified_as_pending_when_enabled(self):
        config = SimpleNamespace(
            lotto=(LottoTicket(round=1224, numbers=(9, 12, 13, 33, 35, 43), label="로또 1224회 A"),),
            pension=(),
        )

        with patch("dhlottery_checker.runner.load_ticket_config", return_value=config):
            with patch("dhlottery_checker.runner.fetch_lotto_winning", side_effect=HttpTimeoutError("1분 초과")):
                with patch("dhlottery_checker.runner.send_kakao_text") as send_kakao:
                    with patch("builtins.print") as print_mock:
                        result = _run_check(self._args(force_notify=False, notify_pending=True))

        self.assertEqual(result, 0)
        send_kakao.assert_called_once()
        message = send_kakao.call_args.args[0]
        self.assertIn("로또 1224회. 아직 당첨결과 발표 전입니다.", message)
        output = "\n".join(call.args[0] for call in print_mock.call_args_list)
        self.assertIn("아직 당첨결과 발표 전입니다", output)

    def test_pending_notice_is_sent_with_resolved_results(self):
        resolved = Outcome("lotto", 1223, "로또 1223회 A", "로또 1223회 A. 미당첨.", "old-ticket", True)
        pending = Outcome(
            "lotto",
            1224,
            "로또 1224회 A",
            "로또 1224회 A. 결과 대기 중입니다.",
            "pending-ticket",
            False,
        )

        with patch("dhlottery_checker.runner.load_ticket_config", return_value=SimpleNamespace(lotto=[], pension=[])):
            with patch("dhlottery_checker.runner._build_outcomes", return_value=[resolved, pending]):
                with patch("dhlottery_checker.runner.send_kakao_text") as send_kakao:
                    with patch("builtins.print"):
                        result = _run_check(self._args(force_notify=False, notify_pending=True))

        self.assertEqual(result, 0)
        self.assertEqual(send_kakao.call_count, 3)
        sent_text = "\n\n".join(call.args[0] for call in send_kakao.call_args_list)
        self.assertIn("로또 1223회. 당첨 0개, 미당첨 1개.", sent_text)
        self.assertIn("로또 1224회. 아직 당첨결과 발표 전입니다.", sent_text)

    def test_status_json_recommends_clear_after_resolved_notification(self):
        status_path = Path(self.temp_dir.name) / "check-status.json"
        outcome = Outcome("lotto", 1223, "로또 1223회 A", "로또 1223회 A. 미당첨.", "done-ticket", True)

        with patch("dhlottery_checker.runner.load_ticket_config", return_value=SimpleNamespace(lotto=[], pension=[])):
            with patch("dhlottery_checker.runner._build_outcomes", return_value=[outcome]):
                with patch("dhlottery_checker.runner.send_kakao_text"):
                    with patch("builtins.print"):
                        result = _run_check(self._args(force_notify=False, status_json=str(status_path)))

        self.assertEqual(result, 0)
        status = json.loads(status_path.read_text(encoding="utf-8"))
        self.assertEqual(status["sent_resolved_count"], 1)
        self.assertEqual(status["pending_count"], 0)
        self.assertTrue(status["clear_tickets"])

    def test_status_json_keeps_tickets_when_pending_remains(self):
        status_path = Path(self.temp_dir.name) / "check-status.json"
        outcome = Outcome(
            "lotto",
            1224,
            "로또 1224회 A",
            "로또 1224회 A. 결과 대기 중입니다.",
            "pending-ticket",
            False,
        )

        with patch("dhlottery_checker.runner.load_ticket_config", return_value=SimpleNamespace(lotto=[], pension=[])):
            with patch("dhlottery_checker.runner._build_outcomes", return_value=[outcome]):
                with patch("dhlottery_checker.runner.send_kakao_text"):
                    with patch("builtins.print"):
                        result = _run_check(self._args(force_notify=False, status_json=str(status_path)))

        self.assertEqual(result, 0)
        status = json.loads(status_path.read_text(encoding="utf-8"))
        self.assertEqual(status["sent_resolved_count"], 0)
        self.assertEqual(status["sent_pending_count"], 0)
        self.assertEqual(status["pending_not_ready_count"], 1)
        self.assertFalse(status["notify_pending"])
        self.assertFalse(status["clear_tickets"])

    def test_status_json_marks_resolved_ticket_removable_when_pending_remains(self):
        status_path = Path(self.temp_dir.name) / "check-status.json"
        resolved = Outcome("pension", 315, "연금복권 315회 1", "연금복권 315회 1. 미당첨.", "done-ticket", True)
        pending = Outcome(
            "pension",
            316,
            "연금복권 316회 1",
            "연금복권 316회 1. 결과 대기 중입니다.",
            "pending-ticket",
            False,
        )

        with patch("dhlottery_checker.runner.load_ticket_config", return_value=SimpleNamespace(lotto=[], pension=[])):
            with patch("dhlottery_checker.runner._build_outcomes", return_value=[resolved, pending]):
                with patch("dhlottery_checker.runner.send_kakao_text"):
                    with patch("builtins.print"):
                        result = _run_check(self._args(force_notify=False, status_json=str(status_path)))

        self.assertEqual(result, 0)
        status = json.loads(status_path.read_text(encoding="utf-8"))
        self.assertEqual(status["sent_resolved_count"], 1)
        self.assertEqual(status["pending_count"], 1)
        self.assertFalse(status["clear_tickets"])
        self.assertEqual(status["removable_resolved_fingerprints"], ["done-ticket"])

    def test_kakao_failure_still_writes_result_history_and_status(self):
        history_path = Path(self.temp_dir.name) / "result-history.yml"
        status_path = Path(self.temp_dir.name) / "check-status.json"
        outcome = Outcome(
            "pension",
            319,
            "연금복권 319회 1",
            "연금복권 319회 1. 7등 1천원.",
            "pension-319",
            True,
            won=True,
            result_label="7등 1천원",
            summary_text="1 1조 780537 7등 1천원",
            detail_header="연금복권 319회 당첨번호 3조 201327, 보너스 각조 632035",
            detail_text="1. 7등 1천원. 내 번호 1조 780537.",
            winning_group=3,
            winning_number="201327",
            bonus_number="632035",
        )

        with patch("dhlottery_checker.runner.load_ticket_config", return_value=SimpleNamespace(lotto=[], pension=[])):
            with patch("dhlottery_checker.runner._build_outcomes", return_value=[outcome]):
                with patch("dhlottery_checker.runner.send_kakao_text", side_effect=HttpError("invalid token")):
                    with patch("builtins.print"):
                        result = _run_check(
                            self._args(
                                force_notify=True,
                                status_json=str(status_path),
                                history=str(history_path),
                            )
                        )

        self.assertEqual(result, 1)
        history = yaml.safe_load(history_path.read_text(encoding="utf-8"))
        self.assertEqual(history["history"][0]["round"], 319)
        self.assertEqual(history["history"][0]["winning_count"], 1)
        status = json.loads(status_path.read_text(encoding="utf-8"))
        self.assertEqual(status["resolved_count"], 1)
        self.assertEqual(status["sent_resolved_count"], 0)
        self.assertIn("invalid token", status["notification_error"])

    def test_kakao_expired_refresh_token_reports_secret_rotation_action(self):
        status_path = Path(self.temp_dir.name) / "check-status.json"
        outcome = Outcome(
            "pension",
            319,
            "연금복권 319회 1",
            "연금복권 319회 1. 7등 1천원.",
            "pension-319",
            True,
            won=True,
            result_label="7등 1천원",
        )
        kakao_error = HttpError(
            "HTTP POST 요청에 실패했습니다. https://kauth.kakao.com/oauth/token. "
            "상태 코드 400, error=invalid_grant, error_code=KOE322, "
            "description=expired_or_invalid_refresh_token"
        )

        with patch("dhlottery_checker.runner.load_ticket_config", return_value=SimpleNamespace(lotto=[], pension=[])):
            with patch("dhlottery_checker.runner._build_outcomes", return_value=[outcome]):
                with patch("dhlottery_checker.runner.send_kakao_text", side_effect=kakao_error):
                    with patch("sys.stderr", new_callable=io.StringIO) as stderr:
                        with patch("sys.stdout", new_callable=io.StringIO):
                            result = _run_check(self._args(force_notify=True, status_json=str(status_path)))

        self.assertEqual(result, 1)
        status = json.loads(status_path.read_text(encoding="utf-8"))
        self.assertIn("카카오톡 토큰 만료", status["notification_error"])
        self.assertIn("KAKAO_REFRESH_TOKEN", status["notification_error"])
        self.assertIn("::error title=카카오톡 토큰 만료::", stderr.getvalue())

    def test_prune_sent_tickets_removes_only_completed_entries(self):
        ticket_path = Path(self.temp_dir.name) / "tickets.yml"
        status_path = Path(self.temp_dir.name) / "check-status.json"
        ticket_path.write_text(
            "\n".join(
                [
                    "pension:",
                    "  tickets:",
                    "    - label: 연금복권 315회 1",
                    "      round: 315",
                    "      group: 1",
                    "      number: '111111'",
                    "    - label: 연금복권 316회 1",
                    "      round: 316",
                    "      group: 1",
                    "      number: '222222'",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        done_fingerprint = fingerprint_ticket(
            {
                "game": "pension",
                "round": 315,
                "group": 1,
                "number": "111111",
                "label": "연금복권 315회 1",
            },
            "",
        )
        status_path.write_text(
            json.dumps({"removable_resolved_fingerprints": [done_fingerprint]}, ensure_ascii=False),
            encoding="utf-8",
        )

        removed = prune_sent_tickets(ticket_path, status_path)

        self.assertEqual(removed, 1)
        updated = ticket_path.read_text(encoding="utf-8")
        self.assertNotIn("315", updated)
        self.assertIn("316", updated)
        self.assertIn("222222", updated)

    def test_prune_sent_tickets_removes_rounds_already_in_result_history(self):
        ticket_path = Path(self.temp_dir.name) / "tickets.yml"
        status_path = Path(self.temp_dir.name) / "missing-check-status.json"
        history_path = Path(self.temp_dir.name) / "result-history.yml"
        ticket_path.write_text(
            "\n".join(
                [
                    "pension:",
                    "  tickets:",
                    "    - label: Pension 316 1",
                    "      round: 316",
                    "      group: 1",
                    "      number: '877478'",
                    "    - label: Pension 317 1",
                    "      round: 317",
                    "      group: 1",
                    "      number: '160446'",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        history_path.write_text(
            yaml.safe_dump(
                {"history": [{"game": "pension", "round": 316, "title": "Pension 316"}]},
                allow_unicode=True,
                sort_keys=False,
            ),
            encoding="utf-8",
        )

        removed = prune_sent_tickets(ticket_path, status_path, history_path)

        self.assertEqual(removed, 1)
        updated = ticket_path.read_text(encoding="utf-8")
        self.assertNotIn("316", updated)
        self.assertNotIn("877478", updated)
        self.assertIn("317", updated)
        self.assertIn("160446", updated)

    def test_write_result_history_summarizes_resolved_groups_without_numbers(self):
        history_path = Path(self.temp_dir.name) / "result-history.yml"
        outcomes = [
            Outcome(
                "lotto",
                1225,
                "로또 1225회 A",
                "로또 1225회 A. 5등 5,000원. 내 번호 1, 2, 3, 4, 5, 6.",
                "lotto-a",
                True,
                won=True,
                result_label="5등 5,000원",
            ),
            Outcome(
                "lotto",
                1225,
                "로또 1225회 B",
                "로또 1225회 B. 미당첨. 내 번호 7, 8, 9, 10, 11, 12.",
                "lotto-b",
                True,
                result_label="미당첨",
            ),
            Outcome(
                "pension",
                316,
                "연금복권 316회 1",
                "연금복권 316회 1. 미당첨. 내 번호 1조 123456.",
                "pension-a",
                True,
                result_label="미당첨",
            ),
        ]

        written = write_result_history(history_path, outcomes, checked_at="2026-05-17T21:45:00+09:00")

        self.assertEqual(written, 2)
        history = history_path.read_text(encoding="utf-8")
        self.assertIn("로또 1225회", history)
        self.assertIn("미당첨 1개, 당첨 5등 1개", history)
        self.assertIn("연금복권 316회", history)
        self.assertIn("미당첨 1개", history)
        self.assertNotIn("1, 2, 3", history)
        self.assertNotIn("123456", history)

    def test_write_result_history_includes_page_result_details(self):
        history_path = Path(self.temp_dir.name) / "result-history.yml"
        outcomes = [
            Outcome(
                "lotto",
                1225,
                "로또 1225회 A",
                "로또 1225회 A. 5등 5,000원. 내 번호 1, 2, 3, 4, 5, 6.",
                "lotto-a",
                True,
                won=True,
                result_label="5등 5,000원",
                match_count=3,
                winning_numbers=(1, 2, 3, 10, 20, 30),
                bonus_number=7,
            ),
            Outcome(
                "pension",
                316,
                "연금복권 316회 1",
                "연금복권 316회 1. 미당첨. 내 번호 1조 123456.",
                "pension-a",
                True,
                result_label="미당첨",
                winning_group=2,
                winning_number="060727",
                bonus_number="293160",
            ),
        ]

        written = write_result_history(history_path, outcomes, checked_at="2026-05-17T21:45:00+09:00")

        self.assertEqual(written, 2)
        data = yaml.safe_load(history_path.read_text(encoding="utf-8"))
        lotto = data["history"][0]
        pension = data["history"][1]
        self.assertEqual(lotto["winning"], {"numbers": [1, 2, 3, 10, 20, 30], "bonus": 7})
        self.assertEqual(
            lotto["tickets"],
            [{"label": "A", "won": True, "result": "5등 5,000원", "match_count": 3}],
        )
        self.assertEqual(
            pension["winning"],
            {"group": 2, "number": "060727", "bonus_number": "293160"},
        )
        self.assertEqual(pension["tickets"], [{"label": "1", "won": False, "result": "미당첨"}])
        history = history_path.read_text(encoding="utf-8")
        self.assertNotIn("1, 2, 3, 4, 5, 6", history)
        self.assertNotIn("123456", history)

    def test_write_result_history_replaces_same_game_round(self):
        history_path = Path(self.temp_dir.name) / "result-history.yml"
        first = [
            Outcome("lotto", 1225, "로또 1225회 A", "A. 미당첨.", "lotto-a", True, result_label="미당첨")
        ]
        second = [
            Outcome("lotto", 1225, "로또 1225회 A", "A. 미당첨.", "lotto-a", True, result_label="미당첨"),
            Outcome("lotto", 1225, "로또 1225회 B", "B. 미당첨.", "lotto-b", True, result_label="미당첨"),
        ]

        write_result_history(history_path, first, checked_at="2026-05-17T21:45:00+09:00")
        write_result_history(history_path, second, checked_at="2026-05-17T21:50:00+09:00")

        data = yaml.safe_load(history_path.read_text(encoding="utf-8"))
        self.assertEqual(len(data["history"]), 1)
        self.assertEqual(data["history"][0]["summary"], "2026.05.17 로또 1225회 미당첨 2개")

    def test_balance_alert_sends_when_balance_is_low(self):
        account_path = Path(self.temp_dir.name) / "account.yml"
        account_path.write_text("balance:\n  amount: 40000\n  currency: KRW\n", encoding="utf-8")

        with patch("dhlottery_checker.runner.send_kakao_text") as send_kakao:
            with patch("builtins.print"):
                result = _run_balance_alert(self._balance_args(account_path))

        self.assertEqual(result, 0)
        send_kakao.assert_called_once()
        self.assertIn("현재 예치금 40,000원", send_kakao.call_args.args[0])

    def test_balance_alert_skips_when_balance_is_sufficient(self):
        account_path = Path(self.temp_dir.name) / "account.yml"
        account_path.write_text("balance:\n  amount: 60000\n  currency: KRW\n", encoding="utf-8")

        with patch("dhlottery_checker.runner.send_kakao_text") as send_kakao:
            with patch("builtins.print"):
                result = _run_balance_alert(self._balance_args(account_path))

        self.assertEqual(result, 0)
        send_kakao.assert_not_called()

    def test_balance_alert_deduplicates_same_low_amount(self):
        account_path = Path(self.temp_dir.name) / "account.yml"
        account_path.write_text("balance:\n  amount: 40000\n  currency: KRW\n", encoding="utf-8")
        args = self._balance_args(account_path)

        with patch("dhlottery_checker.runner.send_kakao_text") as send_kakao:
            with patch("builtins.print"):
                _run_balance_alert(args)
                _run_balance_alert(args)

        send_kakao.assert_called_once()

    def test_check_returns_input_error_for_invalid_ticket_config(self):
        with patch("dhlottery_checker.runner.load_ticket_config", side_effect=ValueError("bad ticket")):
            with patch("builtins.print") as print_mock:
                result = _run_check(self._args(force_notify=False))

        self.assertEqual(result, 2)
        self.assertIn("구매번호 설정 오류", print_mock.call_args.args[0])

    def _args(
        self,
        force_notify: bool,
        status_json: str | None = None,
        notify_pending: bool = False,
        history: str | None = None,
    ) -> argparse.Namespace:
        return argparse.Namespace(
            tickets="unused.yml",
            game="all",
            notify=True,
            dry_run=False,
            state=str(self.state_path),
            no_state=False,
            force_notify=force_notify,
            notify_pending=notify_pending,
            status_json=status_json,
            history=history,
        )

    def _balance_args(self, account_path: Path) -> argparse.Namespace:
        return argparse.Namespace(
            account=str(account_path),
            threshold=50000,
            charge_amount=50000,
            notify=True,
            dry_run=False,
            state=str(Path(self.temp_dir.name) / "balance-alert.json"),
            no_state=False,
            force_notify=False,
        )

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.state_path = Path(self.temp_dir.name) / "sent-results.json"

    def tearDown(self):
        self.temp_dir.cleanup()


if __name__ == "__main__":
    unittest.main()
