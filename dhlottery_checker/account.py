# 동행복권 예치금 스냅샷을 읽고 부족 알림 문구를 만드는 모듈
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


DHLOTTERY_MAIN_URL = "https://www.dhlottery.co.kr/main"
DEFAULT_BALANCE_THRESHOLD = 50_000
DEFAULT_CHARGE_AMOUNT = 50_000


@dataclass(frozen=True)
class AccountSnapshot:
    amount: int
    currency: str = "KRW"
    updated_at: str = ""


def load_account_snapshot(path: str | Path = "data/account.yml") -> AccountSnapshot:
    account_path = Path(path)
    if not account_path.exists():
        raise ValueError(f"예치금 스냅샷 파일이 없습니다. {account_path}")

    source = yaml.safe_load(account_path.read_text(encoding="utf-8")) or {}
    if not isinstance(source, dict):
        raise ValueError("예치금 스냅샷은 YAML 객체여야 합니다.")
    balance = source.get("balance", {})
    if not isinstance(balance, dict):
        raise ValueError("balance 설정은 YAML 객체여야 합니다.")

    try:
        amount = int(balance.get("amount"))
    except (TypeError, ValueError) as exc:
        raise ValueError("balance.amount는 숫자여야 합니다.") from exc
    if amount < 0:
        raise ValueError("balance.amount는 0 이상이어야 합니다.")

    currency = str(balance.get("currency", "KRW")).strip() or "KRW"
    updated_at = str(balance.get("updated_at", "")).strip()
    return AccountSnapshot(amount=amount, currency=currency, updated_at=updated_at)


def needs_balance_charge(snapshot: AccountSnapshot, threshold: int = DEFAULT_BALANCE_THRESHOLD) -> bool:
    return snapshot.amount <= threshold


def format_balance_alert(
    snapshot: AccountSnapshot,
    *,
    threshold: int = DEFAULT_BALANCE_THRESHOLD,
    charge_amount: int = DEFAULT_CHARGE_AMOUNT,
) -> str:
    if needs_balance_charge(snapshot, threshold):
        return "\n".join(
            [
                "[동행복권 예치금 알림]",
                f"현재 예치금 {snapshot.amount:,}원. 기준 {threshold:,}원 이하입니다.",
                f"충전 권장 금액 {charge_amount:,}원.",
                "동행복권에서 직접 확인 후 충전해 주세요.",
                DHLOTTERY_MAIN_URL,
            ]
        )
    return "\n".join(
        [
            "[동행복권 예치금 알림]",
            f"현재 예치금 {snapshot.amount:,}원. 기준 {threshold:,}원보다 높습니다.",
        ]
    )


def balance_state_payload(
    snapshot: AccountSnapshot,
    *,
    threshold: int = DEFAULT_BALANCE_THRESHOLD,
    charge_amount: int = DEFAULT_CHARGE_AMOUNT,
) -> dict[str, Any]:
    return {
        "kind": "balance-low",
        "amount": snapshot.amount,
        "currency": snapshot.currency,
        "threshold": threshold,
        "charge_amount": charge_amount,
    }
