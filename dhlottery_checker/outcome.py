# 당첨 확인 결과와 게임별 표시 이름을 관리하는 모듈
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Outcome:
    game: str
    round: int
    label: str
    text: str
    fingerprint: str
    resolved: bool
    won: bool = False
    result_label: str = ""
    match_count: int | None = None
    summary_text: str = ""
    detail_header: str = ""
    detail_text: str = ""
    winning_numbers: tuple[int, ...] = ()
    bonus_number: int | str | None = None
    winning_group: int | None = None
    winning_number: str = ""


def group_outcomes(outcomes: list[Outcome]) -> list[list[Outcome]]:
    groups: list[list[Outcome]] = []
    indexes: dict[tuple[str, int], int] = {}
    for outcome in outcomes:
        key = (outcome.game, outcome.round)
        if key not in indexes:
            indexes[key] = len(groups)
            groups.append([])
        groups[indexes[key]].append(outcome)
    return groups


def group_title(outcome: Outcome) -> str:
    if outcome.game == "lotto":
        return f"로또 {outcome.round}회"
    if outcome.game == "pension":
        return f"연금복권 {outcome.round}회"
    return f"{outcome.game} {outcome.round}회"


def short_label(label: str, game: str, round_no: int) -> str:
    prefixes = []
    if game == "lotto":
        prefixes.append(f"로또 {round_no}회 ")
    if game == "pension":
        prefixes.append(f"연금복권 {round_no}회 ")
    for prefix in prefixes:
        if label.startswith(prefix):
            return label[len(prefix):]
    return label
