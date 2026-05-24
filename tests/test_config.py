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

    def test_rejects_non_numeric_lotto_number_with_clear_error(self):
        os.environ["TICKETS_YAML"] = """
lotto:
  tickets:
    - round: 1222
      numbers: [1, 2, bad, 4, 5, 6]
"""

        with self.assertRaisesRegex(ValueError, "로또 numbers"):
            load_ticket_config()

    def test_rejects_non_numeric_pension_group_with_clear_error(self):
        os.environ["TICKETS_YAML"] = """
pension:
  tickets:
    - round: 314
      group: bad
      number: "060727"
"""

        with self.assertRaisesRegex(ValueError, "연금복권 group"):
            load_ticket_config()


if __name__ == "__main__":
    unittest.main()
