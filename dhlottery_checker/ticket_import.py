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


@dataclass(frozen=True)
class ImportedPensionTicket:
    round: int
    slot: str
    group: int
    number: str

    @property
    def label(self) -> str:
        return f"연금복권 {self.round}회 {self.slot}"

    def to_yaml_item(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "round": self.round,
            "group": self.group,
            "number": self.number,
        }


@dataclass(frozen=True)
class ImportedTickets:
    lotto: tuple[ImportedLottoTicket, ...] = ()
    pension: tuple[ImportedPensionTicket, ...] = ()

    @property
    def total_count(self) -> int:
        return len(self.lotto) + len(self.pension)


def parse_ticket_text(text: str) -> ImportedTickets:
    lotto_tickets: list[ImportedLottoTicket] = []
    pension_tickets: list[ImportedPensionTicket] = []

    try:
        lotto_tickets = parse_lotto_ticket_text(text)
    except ValueError:
        lotto_tickets = []

    try:
        pension_tickets = parse_pension_ticket_text(text)
    except ValueError:
        pension_tickets = []

    if not lotto_tickets and not pension_tickets:
        raise ValueError("로또 또는 연금복권 티켓 보기 번호를 찾지 못했습니다.")
    return ImportedTickets(tuple(lotto_tickets), tuple(pension_tickets))


def parse_lotto_ticket_text(text: str) -> list[ImportedLottoTicket]:
    lines = _clean_lines(text)
    round_no = _parse_round(lines)
    block_tickets = _parse_lotto_blocks(lines, round_no)
    if block_tickets:
        return block_tickets

    simple_ticket = _parse_simple_lotto(lines, round_no)
    if simple_ticket is not None:
        return [simple_ticket]

    has_lotto_marker = any("로또6/45" in line or "Lotto 6/45" in line or "Lotto6/45" in line for line in lines)
    if not has_lotto_marker:
        raise ValueError("로또 회차와 1부터 45 사이의 숫자 6개를 찾지 못했습니다.")

    tickets = _parse_lotto_rows(lines, round_no)
    if not tickets:
        raise ValueError("선택번호 줄을 찾지 못했습니다. 티켓 보기에서 `A 자동 9 12 13 33 35 43`처럼 보이는 줄까지 복사하세요.")
    return tickets


def parse_pension_ticket_text(text: str) -> list[ImportedPensionTicket]:
    lines = _clean_lines(text)
    round_no = _parse_pension_round(lines)
    tickets = _parse_pension_blocks(lines, round_no)
    if not tickets:
        raise ValueError("연금복권 조와 6자리 번호를 찾지 못했습니다.")
    return tickets


def write_lotto_tickets(
    ticket_path: str | Path,
    imported_tickets: list[ImportedLottoTicket],
    *,
    replace_all: bool = False,
    replace_lotto: bool = False,
) -> None:
    write_tickets(
        ticket_path,
        lotto_tickets=imported_tickets,
        replace_all=replace_all,
        replace_lotto=replace_lotto,
    )


def write_tickets(
    ticket_path: str | Path,
    *,
    lotto_tickets: list[ImportedLottoTicket] | tuple[ImportedLottoTicket, ...] = (),
    pension_tickets: list[ImportedPensionTicket] | tuple[ImportedPensionTicket, ...] = (),
    replace_all: bool = False,
    replace_lotto: bool = False,
    replace_pension: bool = False,
) -> None:
    if not lotto_tickets and not pension_tickets:
        raise ValueError("저장할 구매번호가 없습니다.")

    path = Path(ticket_path)
    source = {} if replace_all else _load_yaml(path)

    if lotto_tickets:
        lotto = source.setdefault("lotto", {})
        if not isinstance(lotto, dict):
            raise ValueError("lotto 설정은 YAML 객체여야 합니다.")
        existing_lotto = [] if replace_lotto else _existing_lotto_tickets(lotto)
        lotto["tickets"] = [*existing_lotto, *_unique_lotto_items(existing_lotto, lotto_tickets)]

    if pension_tickets:
        pension = source.setdefault("pension", {})
        if not isinstance(pension, dict):
            raise ValueError("pension 설정은 YAML 객체여야 합니다.")
        existing_pension = [] if replace_pension else _existing_pension_tickets(pension)
        pension["tickets"] = [*existing_pension, *_unique_pension_items(existing_pension, pension_tickets)]

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(source, allow_unicode=True, sort_keys=False), encoding="utf-8")


def write_imported_tickets(
    ticket_path: str | Path,
    imported_tickets: ImportedTickets,
    *,
    replace_all: bool = False,
    replace_lotto: bool = False,
    replace_pension: bool = False,
) -> None:
    write_tickets(
        ticket_path,
        lotto_tickets=imported_tickets.lotto,
        pension_tickets=imported_tickets.pension,
        replace_all=replace_all,
        replace_lotto=replace_lotto,
        replace_pension=replace_pension,
    )


def _clean_lines(text: str) -> list[str]:
    lines = []
    for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        cleaned = line.strip().lstrip("\ufeff")
        if cleaned:
            lines.append(cleaned)
    return lines


def _parse_round(lines: list[str]) -> int:
    for line in lines:
        match = re.search(r"(\d{3,5})\s*회", line)
        if match:
            return int(match.group(1))

    first_line_round = _parse_plain_round(lines)
    if first_line_round is not None:
        return first_line_round

    for index, line in enumerate(lines):
        if "로또6/45" not in line and "Lotto 6/45" not in line and "Lotto6/45" not in line:
            continue
        for candidate in lines[index + 1 : index + 6]:
            if re.fullmatch(r"\d{3,5}", candidate):
                return int(candidate)

    raise ValueError("로또 회차를 찾지 못했습니다.")


def _parse_plain_round(lines: list[str]) -> int | None:
    if not lines:
        return None
    first_line = lines[0]
    if not re.fullmatch(r"\d{3,5}", first_line):
        return None
    remaining_numbers = [token for line in lines[1:] for token in re.findall(r"\d+", line)]
    if len(remaining_numbers) != 6:
        return None
    return int(first_line)


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


def _parse_lotto_blocks(lines: list[str], round_no: int) -> list[ImportedLottoTicket]:
    tickets: list[ImportedLottoTicket] = []
    seen_slots: set[str] = set()

    for index, line in enumerate(lines):
        slot_match = re.fullmatch(r"([A-E])(?:\s+(?:자동|수동|반자동))?(?:\s+(.*))?", line)
        if not slot_match:
            continue

        slot = slot_match.group(1)
        if slot in seen_slots:
            continue

        numbers = _numbers_from_block(slot_match.group(2) or "", lines[index + 1 :])
        parsed = tuple(numbers)
        if not _valid_lotto_numbers(parsed):
            continue

        seen_slots.add(slot)
        tickets.append(ImportedLottoTicket(round_no, slot, parsed))  # type: ignore[arg-type]

    return tickets


def _numbers_from_block(first_line: str, following_lines: list[str]) -> list[int]:
    numbers = _valid_number_tokens(first_line)
    for line in following_lines:
        if len(numbers) >= 6:
            break
        if re.fullmatch(r"[A-E](?:\s+.*)?", line):
            break
        if re.fullmatch(r"자동|수동|반자동", line):
            continue

        tokens = _valid_number_tokens(line)
        if not tokens:
            continue
        numbers.extend(tokens)

    return numbers[:6]


def _valid_number_tokens(line: str) -> list[int]:
    if not line:
        return []
    tokens = re.findall(r"\d+", line)
    if not tokens:
        return []
    if re.sub(r"[\d\s]+", "", line):
        return []

    numbers = [int(token) for token in tokens]
    if any(number < 1 or number > 45 for number in numbers):
        return []
    return numbers


def _parse_simple_lotto(lines: list[str], round_no: int) -> ImportedLottoTicket | None:
    numbers: list[int] = []
    for index, line in enumerate(lines):
        if re.search(r"\d{3,5}\s*회", line) or (index == 0 and re.fullmatch(r"\d{3,5}", line)):
            continue
        tokens = re.findall(r"\d+", line)
        if any(int(token) > 45 for token in tokens):
            return None
        numbers.extend(int(token) for token in tokens if 1 <= int(token) <= 45)

    parsed = tuple(numbers)
    if not _valid_lotto_numbers(parsed):
        return None
    return ImportedLottoTicket(round_no, "A", parsed)  # type: ignore[arg-type]


def _parse_pension_round(lines: list[str]) -> int:
    first_group_index = next((index for index, line in enumerate(lines) if re.fullmatch(r"[1-5]\s*조", line)), None)
    if first_group_index is not None:
        for line in reversed(lines[:first_group_index]):
            if "/" in line or ":" in line:
                continue
            match = re.search(r"(\d{1,5})\s*회", line) or re.fullmatch(r"\D*(\d{1,5})(?:\D|$)", line)
            if match:
                return int(match.group(1))

    for line in lines:
        if "/" in line or ":" in line:
            continue
        match = re.match(r"\D*(\d{1,5})(?:\D|$)", line)
        if match:
            return int(match.group(1))

    for line in lines:
        match = re.search(r"(\d{1,5})\s*회", line)
        if match:
            return int(match.group(1))

    raise ValueError("연금복권 회차를 찾지 못했습니다.")


def _parse_pension_blocks(lines: list[str], round_no: int) -> list[ImportedPensionTicket]:
    tickets: list[ImportedPensionTicket] = []
    for index, line in enumerate(lines):
        group_match = re.fullmatch(r"([1-5])\s*조", line)
        if not group_match:
            continue

        digits = _pension_digits_from_block(lines[index + 1 :])
        if len(digits) != 6:
            continue
        tickets.append(
            ImportedPensionTicket(
                round=round_no,
                slot=str(len(tickets) + 1),
                group=int(group_match.group(1)),
                number="".join(digits),
            )
        )
    return tickets


def _pension_digits_from_block(following_lines: list[str]) -> list[str]:
    digits: list[str] = []
    for line in following_lines:
        if len(digits) >= 6:
            break
        if re.fullmatch(r"[1-5]\s*조", line):
            break
        single_digit = re.fullmatch(r"(\d)\D*", line)
        if single_digit:
            digits.append(single_digit.group(1))
            continue
        if re.fullmatch(r"\d{6}", line):
            digits.extend(line)
    return digits[:6]


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


def _existing_pension_tickets(pension: dict[str, Any]) -> list[dict[str, Any]]:
    tickets = pension.get("tickets", [])
    if tickets is None:
        return []
    if not isinstance(tickets, list):
        raise ValueError("pension.tickets 설정은 목록이어야 합니다.")
    return [item for item in tickets if isinstance(item, dict)]


def _unique_lotto_items(
    existing: list[dict[str, Any]],
    imported_tickets: list[ImportedLottoTicket] | tuple[ImportedLottoTicket, ...],
) -> list[dict[str, Any]]:
    existing_keys = {_lotto_key(item) for item in existing}
    new_items = []
    for ticket in imported_tickets:
        item = ticket.to_yaml_item()
        key = _lotto_key(item)
        if key not in existing_keys:
            new_items.append(item)
            existing_keys.add(key)
    return new_items


def _unique_pension_items(
    existing: list[dict[str, Any]],
    imported_tickets: list[ImportedPensionTicket] | tuple[ImportedPensionTicket, ...],
) -> list[dict[str, Any]]:
    existing_keys = {_pension_key(item) for item in existing}
    new_items = []
    for ticket in imported_tickets:
        item = ticket.to_yaml_item()
        key = _pension_key(item)
        if key not in existing_keys:
            new_items.append(item)
            existing_keys.add(key)
    return new_items


def _lotto_key(item: dict[str, Any]) -> tuple[int | str | None, tuple[int, ...]]:
    numbers = item.get("numbers", [])
    if isinstance(numbers, list):
        parsed_numbers = tuple(int(number) for number in numbers)
    else:
        parsed_numbers = ()
    return item.get("round"), parsed_numbers


def _pension_key(item: dict[str, Any]) -> tuple[int | str | None, int | None, str]:
    try:
        group = int(item.get("group"))
    except (TypeError, ValueError):
        group = None
    return item.get("round"), group, str(item.get("number", "")).strip()
