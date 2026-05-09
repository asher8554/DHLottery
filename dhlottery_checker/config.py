# 구매번호 설정을 읽고 검증하는 모듈
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Any

import yaml


RoundValue = int | str


@dataclass(frozen=True)
class LottoTicket:
    round: RoundValue
    numbers: tuple[int, int, int, int, int, int]
    label: str = ""

    def state_payload(self) -> dict[str, Any]:
        return {
            "game": "lotto",
            "round": self.round,
            "numbers": list(self.numbers),
            "label": self.label,
        }


@dataclass(frozen=True)
class PensionTicket:
    round: RoundValue
    group: int
    number: str
    label: str = ""

    def state_payload(self) -> dict[str, Any]:
        return {
            "game": "pension",
            "round": self.round,
            "group": self.group,
            "number": self.number,
            "label": self.label,
        }


@dataclass(frozen=True)
class TicketConfig:
    lotto: tuple[LottoTicket, ...]
    pension: tuple[PensionTicket, ...]


def load_ticket_config(path: str | Path | None = None) -> TicketConfig:
    raw_text = os.environ.get("TICKETS_YAML")
    if raw_text:
        source = yaml.safe_load(raw_text) or {}
    else:
        ticket_path = Path(path or "tickets.yml")
        if not ticket_path.exists():
            raise ValueError(f"구매번호 설정 파일이 없습니다. {ticket_path}")
        source = yaml.safe_load(ticket_path.read_text(encoding="utf-8")) or {}

    if not isinstance(source, dict):
        raise ValueError("구매번호 설정은 YAML 객체여야 합니다.")

    return TicketConfig(
        lotto=tuple(_parse_lotto_ticket(item) for item in _ticket_items(source, "lotto")),
        pension=tuple(_parse_pension_ticket(item) for item in _ticket_items(source, "pension")),
    )


def _ticket_items(source: dict[str, Any], key: str) -> list[dict[str, Any]]:
    section = source.get(key, {})
    if section is None:
        return []
    if not isinstance(section, dict):
        raise ValueError(f"{key} 설정은 객체여야 합니다.")
    tickets = section.get("tickets", [])
    if tickets is None:
        return []
    if not isinstance(tickets, list):
        raise ValueError(f"{key}.tickets 설정은 목록이어야 합니다.")
    for ticket in tickets:
        if not isinstance(ticket, dict):
            raise ValueError(f"{key}.tickets 항목은 객체여야 합니다.")
    return tickets


def _parse_round(value: Any) -> RoundValue:
    if isinstance(value, str) and value.strip().lower() == "latest":
        return "latest"
    if isinstance(value, int) and value > 0:
        return value
    raise ValueError("round는 양의 정수 또는 latest여야 합니다.")


def _parse_lotto_ticket(item: dict[str, Any]) -> LottoTicket:
    numbers = item.get("numbers")
    if not isinstance(numbers, list) or len(numbers) != 6:
        raise ValueError("로또 numbers는 숫자 6개 목록이어야 합니다.")
    parsed = tuple(int(number) for number in numbers)
    if len(set(parsed)) != 6 or any(number < 1 or number > 45 for number in parsed):
        raise ValueError("로또 numbers는 1부터 45까지의 중복 없는 숫자 6개여야 합니다.")

    return LottoTicket(
        round=_parse_round(item.get("round")),
        numbers=parsed,  # type: ignore[arg-type]
        label=str(item.get("label", "")).strip(),
    )


def _parse_pension_ticket(item: dict[str, Any]) -> PensionTicket:
    group = int(item.get("group"))
    number = str(item.get("number", "")).strip()
    if group < 1 or group > 5:
        raise ValueError("연금복권 group은 1부터 5까지여야 합니다.")
    if len(number) != 6 or not number.isdigit():
        raise ValueError("연금복권 number는 6자리 숫자 문자열이어야 합니다.")

    return PensionTicket(
        round=_parse_round(item.get("round")),
        group=group,
        number=number,
        label=str(item.get("label", "")).strip(),
    )

