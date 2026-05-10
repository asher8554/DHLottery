# 검사 실행기의 중복 알림 처리 옵션을 검증하는 테스트
from __future__ import annotations

import argparse
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from dhlottery_checker.runner import Outcome, _run_check


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
                            send_kakao.assert_called_once()
                            self.assertIn("재전송 결과", send_kakao.call_args.args[0])

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
