# 연금복권720+ 당첨번호 조회와 등수 계산을 담당하는 모듈
from __future__ import annotations

from dataclasses import dataclass

from .http import get_json


PENSION_LIST_API = "https://www.dhlottery.co.kr/pt720/selectPstPt720WnList.do"

PENSION_PRIZE_LABELS = {
    "1등": "월 700만원 x 20년",
    "2등": "월 100만원 x 10년",
    "3등": "100만원",
    "4등": "10만원",
    "5등": "5만원",
    "6등": "5천원",
    "7등": "1천원",
    "보너스": "월 100만원 x 10년",
}


class ResultNotReady(RuntimeError):
    pass


@dataclass(frozen=True)
class PensionWinning:
    round: int
    draw_date: str
    group: int
    number: str
    bonus_number: str


@dataclass(frozen=True)
class PensionMatch:
    rank_label: str
    amount_label: str


def fetch_pension_winnings() -> tuple[PensionWinning, ...]:
    payload = get_json(PENSION_LIST_API)
    items = payload.get("data", {}).get("result", [])
    winnings = tuple(_winning_from_item(item) for item in items)
    if not winnings:
        raise ResultNotReady("연금복권 결과 목록이 비어 있습니다.")
    return winnings


def fetch_latest_pension_round() -> int:
    return fetch_pension_winnings()[0].round


def fetch_pension_winning(round_no: int) -> PensionWinning:
    for winning in fetch_pension_winnings():
        if winning.round == round_no:
            return winning
    raise ResultNotReady(f"연금복권 {round_no}회 결과가 아직 조회되지 않습니다.")


def check_pension(group: int, number: str, winning: PensionWinning) -> tuple[PensionMatch, ...]:
    matches: list[PensionMatch] = []

    if group == winning.group and number == winning.number:
        matches.append(_match("1등"))
    elif group != winning.group and number == winning.number:
        matches.append(_match("2등"))
    else:
        for rank, suffix_len in (("3등", 5), ("4등", 4), ("5등", 3), ("6등", 2), ("7등", 1)):
            if number[-suffix_len:] == winning.number[-suffix_len:]:
                matches.append(_match(rank))
                break

    if number == winning.bonus_number:
        matches.append(_match("보너스"))

    return tuple(matches)


def _match(rank_label: str) -> PensionMatch:
    return PensionMatch(rank_label=rank_label, amount_label=PENSION_PRIZE_LABELS[rank_label])


def _winning_from_item(item: dict[str, object]) -> PensionWinning:
    return PensionWinning(
        round=int(item["psltEpsd"]),
        draw_date=_format_yyyymmdd(str(item["psltRflYmd"])),
        group=int(item["wnBndNo"]),
        number=str(item["wnRnkVl"]).zfill(6),
        bonus_number=str(item["bnsRnkVl"]).zfill(6),
    )


def _format_yyyymmdd(value: str) -> str:
    if len(value) == 8 and value.isdigit():
        return f"{value[:4]}-{value[4:6]}-{value[6:]}"
    return value

