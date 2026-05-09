# 중복 알림 방지용 지문 생성을 검증하는 테스트
import unittest

from dhlottery_checker.state import fingerprint_ticket


class StateTest(unittest.TestCase):
    def test_fingerprint_uses_salt(self):
        payload = {"game": "lotto", "round": 1222, "numbers": [1, 2, 3, 4, 5, 6]}
        self.assertNotEqual(fingerprint_ticket(payload), fingerprint_ticket(payload, "secret"))


if __name__ == "__main__":
    unittest.main()

