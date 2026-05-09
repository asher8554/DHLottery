# 로또 6/45 당첨번호 조회와 등수 계산을 담당하는 모듈
from __future__ import annotations

from dataclasses import dataclass
import re

from .http import get_json, get_text


LOTTO_RESULT_PAGE = "https://www.dhlottery.co.kr/lt645/result"
LOTTO_RESULT_API = "https://www.dhlottery.co.kr/lt645/selectPstLt645InfoNew.do"


class ResultNotReady(RuntimeError):
    pass


@dataclass(frozen=True)
class LottoWinning:
    round: int
    draw_date: str
    numbers: tuple[int, int, int, int, int, int]
    bonus: int
    prize_by_rank: dict[int, int]


@dataclass(frozen=True)
class LottoMatch:
    rank: int | None
    matched_count: int
    matched_bonus: bool
    amount: int | None

    @property
    def is_winner(self) -> bool:
        return self.rank is not None


def fetch_latest_lotto_round() -> int:
    html = get_text(LOTTO_RESULT_PAGE)
    match = re.search(r'id="opt_val"\s+value="(\d+)"', html)
    if not match:
        match = re.search(r'value="(\d+)">\s*회차선택', html)
    if not match:
        raise ResultNotReady("최신 로또 회차를 찾지 못했습니다.")
    return int(match.group(1))


def fetch_lotto_winning(round_no: int) -> LottoWinning:
    payload = get_json(
        LOTTO_RESULT_API,
        {
            "srchDir": "center",
            "srchLtEpsd": round_no,
        },
    )
    items = payload.get("data", {}).get("list", [])
    for item in items:
        if int(item.get("ltEpsd", 0)) == round_no:
            return _winning_from_item(item)
    raise ResultNotReady(f"로또 {round_no}회 결과가 아직 조회되지 않습니다.")


def check_lotto(numbers: tuple[int, int, int, int, int, int], winning: LottoWinning) -> LottoMatch:
    selected = set(numbers)
    winning_numbers = set(winning.numbers)
    matched_count = len(selected & winning_numbers)
    matched_bonus = winning.bonus in selected

    rank = None
    if matched_count == 6:
        rank = 1
    elif matched_count == 5 and matched_bonus:
        rank = 2
    elif matched_count == 5:
        rank = 3
    elif matched_count == 4:
        rank = 4
    elif matched_count == 3:
        rank = 5

    return LottoMatch(
        rank=rank,
        matched_count=matched_count,
        matched_bonus=matched_bonus,
        amount=winning.prize_by_rank.get(rank) if rank else None,
    )


def format_lotto_numbers(numbers: tuple[int, ...]) -> str:
    return ", ".join(str(number) for number in numbers)


def _winning_from_item(item: dict[str, object]) -> LottoWinning:
    return LottoWinning(
        round=int(item["ltEpsd"]),
        draw_date=_format_yyyymmdd(str(item["ltRflYmd"])),
        numbers=tuple(int(item[f"tm{idx}WnNo"]) for idx in range(1, 7)),  # type: ignore[arg-type]
        bonus=int(item["bnsWnNo"]),
        prize_by_rank={
            rank: int(item.get(f"rnk{rank}WnAmt", 0))
            for rank in range(1, 6)
        },
    )


def _format_yyyymmdd(value: str) -> str:
    if len(value) == 8 and value.isdigit():
        return f"{value[:4]}-{value[4:6]}-{value[6:]}"
    return value

