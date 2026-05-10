# 예치금 스냅샷 파싱과 부족 알림 문구를 검증하는 테스트
from pathlib import Path
import tempfile
import unittest

from dhlottery_checker.account import (
    AccountSnapshot,
    balance_state_payload,
    format_balance_alert,
    load_account_snapshot,
    needs_balance_charge,
)


class AccountTest(unittest.TestCase):
    def test_loads_account_snapshot(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "account.yml"
            path.write_text(
                'balance:\n  amount: 40000\n  currency: KRW\n  updated_at: "2026-05-10T14:40:20Z"\n',
                encoding="utf-8",
            )

            snapshot = load_account_snapshot(path)

        self.assertEqual(snapshot.amount, 40000)
        self.assertEqual(snapshot.currency, "KRW")
        self.assertEqual(snapshot.updated_at, "2026-05-10T14:40:20Z")

    def test_detects_low_balance_at_threshold(self):
        self.assertTrue(needs_balance_charge(AccountSnapshot(amount=50000), 50000))
        self.assertFalse(needs_balance_charge(AccountSnapshot(amount=50001), 50000))

    def test_formats_low_balance_alert(self):
        message = format_balance_alert(AccountSnapshot(amount=40000), threshold=50000, charge_amount=50000)

        self.assertIn("[동행복권 예치금 알림]", message)
        self.assertIn("현재 예치금 40,000원. 기준 50,000원 이하입니다.", message)
        self.assertIn("충전 권장 금액 50,000원.", message)
        self.assertIn("동행복권에서 직접 확인 후 충전해 주세요.", message)

    def test_formats_sufficient_balance_message(self):
        message = format_balance_alert(AccountSnapshot(amount=60000), threshold=50000)

        self.assertIn("현재 예치금 60,000원. 기준 50,000원보다 높습니다.", message)
        self.assertNotIn("충전 권장", message)

    def test_balance_state_payload_ignores_updated_at(self):
        first = balance_state_payload(AccountSnapshot(amount=40000, updated_at="one"), threshold=50000)
        second = balance_state_payload(AccountSnapshot(amount=40000, updated_at="two"), threshold=50000)

        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
