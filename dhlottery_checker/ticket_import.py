# 동행복권 티켓 보기 텍스트를 구매번호 YAML로 변환하는 모듈
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any

import yaml


LOTTO_GAME_ROW_RE = re.compile(
    r"(?:^|\s)([A-E])\s*(?:자동|수동|반자동)?\s+"
    r"(\d{1,2})\s+(\d{1,2})\s+(\d{1,2})\s+(\d{1,2})\s+(\d{1,2})\s+(\d{1,2})(?:\s|$)"
)


@dataclass(frozen=True)
class ImportedLottoTicket:
    round: int
    slot: str
    numbers: tuple[int, int, int, int, int, int]

    @property
    def label(self) -> str:
        return f"로또 {self.round}회 {self.slot}"

    def to_yaml_item(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "round": self.round,
            "numbers": list(self.numbers),
        }


def parse_lotto_ticket_text(text: str) -> list[ImportedLottoTicket]:
    lines = _clean_lines(text)
    if not any("로또6/45" in line or "Lotto 6/45" in line or "Lotto6/45" in line for line in lines):
        raise ValueError("로또6/45 티켓 텍스트를 찾지 못했습니다.")

    round_no = _parse_round(lines)
    tickets = _parse_lotto_rows(lines, round_no)
    if not tickets:
        raise ValueError("선택번호 줄을 찾지 못했습니다. 티켓 보기에서 `A 자동 9 12 13 33 35 43`처럼 보이는 줄까지 복사하세요.")
    return tickets


def write_lotto_tickets(
    ticket_path: str | Path,
    imported_tickets: list[ImportedLottoTicket],
    *,
    replace_all: bool = False,
    replace_lotto: bool = False,
) -> None:
    if not imported_tickets:
        raise ValueError("저장할 로또 티켓이 없습니다.")

    path = Path(ticket_path)
    source = {} if replace_all else _load_yaml(path)
    lotto = source.setdefault("lotto", {})
    if not isinstance(lotto, dict):
        raise ValueError("lotto 설정은 YAML 객체여야 합니다.")

    existing = [] if replace_lotto else _existing_lotto_tickets(lotto)
    existing_keys = {_lotto_key(item) for item in existing}
    new_items = []
    for ticket in imported_tickets:
        item = ticket.to_yaml_item()
        key = _lotto_key(item)
        if key not in existing_keys:
            new_items.append(item)
            existing_keys.add(key)

    lotto["tickets"] = [*existing, *new_items]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(source, allow_unicode=True, sort_keys=False), encoding="utf-8")


def _clean_lines(text: str) -> list[str]:
    return [line.strip() for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n") if line.strip()]


def _parse_round(lines: list[str]) -> int:
    for line in lines:
        match = re.search(r"(\d{3,5})\s*회", line)
        if match:
            return int(match.group(1))

    for index, line in enumerate(lines):
        if "로또6/45" not in line and "Lotto 6/45" not in line and "Lotto6/45" not in line:
            continue
        for candidate in lines[index + 1 : index + 6]:
            if re.fullmatch(r"\d{3,5}", candidate):
                return int(candidate)

    raise ValueError("로또 회차를 찾지 못했습니다.")


def _parse_lotto_rows(lines: list[str], round_no: int) -> list[ImportedLottoTicket]:
    tickets: list[ImportedLottoTicket] = []
    seen: set[tuple[str, tuple[int, int, int, int, int, int]]] = set()

    for index in range(len(lines)):
        window = " ".join(lines[index : index + 3])
        for match in LOTTO_GAME_ROW_RE.finditer(window):
            slot = match.group(1)
            numbers = tuple(int(match.group(group)) for group in range(2, 8))
            if not _valid_lotto_numbers(numbers):
                continue
            key = (slot, numbers)
            if key in seen:
                continue
            seen.add(key)
            tickets.append(ImportedLottoTicket(round_no, slot, numbers))  # type: ignore[arg-type]

    return tickets


def _valid_lotto_numbers(numbers: tuple[int, ...]) -> bool:
    return len(numbers) == 6 and len(set(numbers)) == 6 and all(1 <= number <= 45 for number in numbers)


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    source = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(source, dict):
        raise ValueError("구매번호 설정은 YAML 객체여야 합니다.")
    return source


def _existing_lotto_tickets(lotto: dict[str, Any]) -> list[dict[str, Any]]:
    tickets = lotto.get("tickets", [])
    if tickets is None:
        return []
    if not isinstance(tickets, list):
        raise ValueError("lotto.tickets 설정은 목록이어야 합니다.")
    return [item for item in tickets if isinstance(item, dict)]


def _lotto_key(item: dict[str, Any]) -> tuple[int | str | None, tuple[int, ...]]:
    numbers = item.get("numbers", [])
    if isinstance(numbers, list):
        parsed_numbers = tuple(int(number) for number in numbers)
    else:
        parsed_numbers = ()
    return item.get("round"), parsed_numbers
