# 구매번호 YAML 설정 검증을 확인하는 테스트
import os
import unittest

from dhlottery_checker.config import load_ticket_config


class ConfigTest(unittest.TestCase):
    def tearDown(self):
        os.environ.pop("TICKETS_YAML", None)

    def test_loads_from_environment(self):
        os.environ["TICKETS_YAML"] = """
lotto:
  tickets:
    - round: 1222
      numbers: [4, 11, 17, 22, 32, 41]
pension:
  tickets:
    - round: 314
      group: 2
      number: "060727"
"""
        config = load_ticket_config()
        self.assertEqual(config.lotto[0].round, 1222)
        self.assertEqual(config.pension[0].number, "060727")


if __name__ == "__main__":
    unittest.main()

