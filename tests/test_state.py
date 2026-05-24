# 중복 알림 방지용 지문 생성을 검증하는 테스트
import json
from pathlib import Path
import tempfile
import unittest

from dhlottery_checker.state import SentState, fingerprint_ticket


class StateTest(unittest.TestCase):
    def test_fingerprint_uses_salt(self):
        payload = {"game": "lotto", "round": 1222, "numbers": [1, 2, 3, 4, 5, 6]}
        self.assertNotEqual(fingerprint_ticket(payload), fingerprint_ticket(payload, "secret"))

    def test_load_ignores_corrupt_json_state(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "sent-results.json"
            path.write_text("{bad", encoding="utf-8")

            state = SentState.load(path)

        self.assertEqual(state.sent, {})

    def test_save_writes_valid_state_json(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "sent-results.json"
            state = SentState(path, {})
            state.mark_sent("abc", "lotto", 1222)

            state.save()

            self.assertIn("abc", json.loads(path.read_text(encoding="utf-8"))["sent"])
            self.assertFalse(path.with_suffix(".json.tmp").exists())


if __name__ == "__main__":
    unittest.main()
