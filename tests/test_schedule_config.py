# 카카오 알림 시간 설정의 실행 대상 시간 판정을 검증하는 테스트
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest

from dhlottery_checker.schedule_config import decide_notification_schedule, load_notification_schedule


class NotificationScheduleConfigTest(unittest.TestCase):
    def test_loads_default_schedule_when_file_is_missing(self):
        schedule = load_notification_schedule(Path(self.temp_dir.name) / "missing.yml")

        self.assertEqual(schedule.timezone, "Asia/Seoul")
        self.assertEqual(schedule.window_minutes, 30)
        self.assertEqual(schedule.games[0].game, "lotto")
        self.assertEqual(schedule.games[0].time_text, "21:45")

    def test_scheduled_lotto_window_is_due(self):
        settings_path = self._settings()
        decision = decide_notification_schedule(
            settings_path,
            now=datetime(2026, 5, 16, 21, 50),
            event_name="schedule",
        )

        self.assertTrue(decision.should_run)
        self.assertEqual(decision.reason, "scheduled_window")
        self.assertEqual(decision.due_games, ("lotto",))

    def test_outside_window_is_skipped(self):
        settings_path = self._settings()
        decision = decide_notification_schedule(
            settings_path,
            now=datetime(2026, 5, 16, 22, 20),
            event_name="schedule",
        )

        self.assertFalse(decision.should_run)
        self.assertEqual(decision.reason, "outside_schedule")
        self.assertEqual(decision.due_games, ())

    def test_manual_dispatch_runs_even_outside_window(self):
        settings_path = self._settings()
        decision = decide_notification_schedule(
            settings_path,
            now=datetime(2026, 5, 16, 10, 0),
            event_name="workflow_dispatch",
        )

        self.assertTrue(decision.should_run)
        self.assertEqual(decision.reason, "manual_dispatch")

    def test_aware_utc_time_is_converted_to_configured_timezone(self):
        settings_path = self._settings()
        decision = decide_notification_schedule(
            settings_path,
            now=datetime(2026, 5, 16, 12, 50, tzinfo=timezone.utc),
            event_name="schedule",
        )

        self.assertTrue(decision.should_run)
        self.assertEqual(decision.local_time.hour, 21)
        self.assertEqual(decision.local_time.minute, 50)

    def _settings(self) -> Path:
        path = Path(self.temp_dir.name) / "notification-settings.yml"
        path.write_text(
            "\n".join(
                [
                    "notification_schedule:",
                    "  timezone: Asia/Seoul",
                    "  window_minutes: 30",
                    "  lotto:",
                    "    enabled: true",
                    "    day: saturday",
                    "    time: \"21:45\"",
                    "  pension:",
                    "    enabled: true",
                    "    day: thursday",
                    "    time: \"20:10\"",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return path

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()


if __name__ == "__main__":
    unittest.main()
