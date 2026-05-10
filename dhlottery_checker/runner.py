# 구매번호를 당첨번호와 비교하고 알림 흐름을 실행하는 모듈
from __future__ import annotations

import argparse
from dataclasses import dataclass
import os
from pathlib import Path
import sys
from typing import Iterable

from .config import LottoTicket, PensionTicket, load_ticket_config
from .kakao import send_kakao_text
from .lotto import (
    ResultNotReady as LottoResultNotReady,
    check_lotto,
    fetch_latest_lotto_round,
    fetch_lotto_winning,
    format_lotto_numbers,
)
from .pension import (
    ResultNotReady as PensionResultNotReady,
    check_pension,
    fetch_latest_pension_round,
    fetch_pension_winning,
)
from .state import SentState, fingerprint_ticket
from .ticket_import import parse_lotto_ticket_text, write_lotto_tickets


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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="동행복권 당첨번호를 확인하고 카카오톡으로 알립니다.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    check_parser = subparsers.add_parser("check", help="구매번호와 당첨번호를 비교합니다.")
    check_parser.add_argument("--tickets", default="tickets.yml", help="로컬 구매번호 YAML 파일 경로입니다.")
    check_parser.add_argument("--game", choices=("all", "lotto", "pension"), default="all", help="확인할 게임입니다.")
    check_parser.add_argument("--notify", action="store_true", help="카카오톡 알림을 보냅니다.")
    check_parser.add_argument("--dry-run", action="store_true", help="카카오톡 알림 없이 결과만 출력합니다.")
    check_parser.add_argument("--state", default=".state/sent-results.json", help="중복 알림 방지 상태 파일입니다.")
    check_parser.add_argument("--no-state", action="store_true", help="중복 알림 방지 상태를 사용하지 않습니다.")
    check_parser.add_argument("--force-notify", action="store_true", help="이미 알린 결과도 이번 실행에 다시 포함합니다.")

    import_parser = subparsers.add_parser("import-ticket", help="동행복권 티켓 보기 텍스트를 구매번호 YAML에 저장합니다.")
    import_parser.add_argument("--input", help="붙여넣기 텍스트 파일 경로입니다. 생략하면 표준 입력을 읽습니다.")
    import_parser.add_argument("--tickets", default="data/tickets.yml", help="갱신할 구매번호 YAML 파일 경로입니다.")
    import_parser.add_argument("--replace-all", action="store_true", help="기존 설정을 모두 지우고 가져온 로또 항목만 저장합니다.")
    import_parser.add_argument("--replace-lotto", action="store_true", help="기존 로또 항목을 지우고 가져온 항목만 저장합니다.")

    args = parser.parse_args(argv)
    if args.command == "check":
        return _run_check(args)
    if args.command == "import-ticket":
        return _run_import_ticket(args)
    return 1


def _run_import_ticket(args: argparse.Namespace) -> int:
    text = Path(args.input).read_text(encoding="utf-8") if args.input else sys.stdin.read()
    try:
        tickets = parse_lotto_ticket_text(text)
        write_lotto_tickets(args.tickets, tickets, replace_all=args.replace_all, replace_lotto=args.replace_lotto)
    except ValueError as exc:
        print(f"입력 오류. {exc}", file=sys.stderr)
        return 2
    summary = ", ".join(" ".join(str(number) for number in ticket.numbers) for ticket in tickets)
    print(f"{args.tickets} 파일을 갱신했습니다. 가져온 로또 {tickets[0].round}회 번호. {summary}")
    return 0


def _run_check(args: argparse.Namespace) -> int:
    config = load_ticket_config(args.tickets)
    state = None if args.no_state else SentState.load(args.state)
    salt = os.environ.get("STATE_HASH_SALT", "")

    outcomes = list(_build_outcomes(config.lotto, config.pension, args.game, salt))
    resolved = [outcome for outcome in outcomes if outcome.resolved]
    unsent = resolved if args.force_notify else [
        outcome for outcome in resolved if state is None or not state.is_sent(outcome.fingerprint)
    ]

    messages = _format_messages(unsent, outcomes)
    print("\n\n".join(messages))

    if args.notify and not args.dry_run and unsent:
        for message in messages:
            send_kakao_text(message)
        if state is not None:
            for outcome in unsent:
                state.mark_sent(outcome.fingerprint, outcome.game, outcome.round)
            state.save()
    elif state is not None and not Path(args.state).exists():
        state.save()

    return 0


def _build_outcomes(
    lotto_tickets: Iterable[LottoTicket],
    pension_tickets: Iterable[PensionTicket],
    game: str,
    salt: str,
) -> Iterable[Outcome]:
    if game in ("all", "lotto"):
        yield from _lotto_outcomes(lotto_tickets, salt)
    if game in ("all", "pension"):
        yield from _pension_outcomes(pension_tickets, salt)


def _lotto_outcomes(tickets: Iterable[LottoTicket], salt: str) -> Iterable[Outcome]:
    latest_round: int | None = None
    winning_cache = {}
    for ticket in tickets:
        round_no = _resolve_round(ticket.round, latest_round, fetch_latest_lotto_round)
        if ticket.round == "latest":
            latest_round = round_no
        fingerprint = fingerprint_ticket({**ticket.state_payload(), "round": round_no}, salt)
        label = ticket.label or f"로또 {round_no}회"
        try:
            if round_no not in winning_cache:
                winning_cache[round_no] = fetch_lotto_winning(round_no)
            winning = winning_cache[round_no]
            match = check_lotto(ticket.numbers, winning)
        except LottoResultNotReady as exc:
            yield Outcome("lotto", round_no, label, f"{label}. 결과 대기 중입니다. {exc}", fingerprint, False)
            continue

        selected = format_lotto_numbers(tuple(sorted(ticket.numbers)))
        winning_text = f"{format_lotto_numbers(winning.numbers)} + 보너스 {winning.bonus}"
        short_label = _short_label(label, "lotto", round_no)
        matched_numbers = tuple(number for number in winning.numbers if number in ticket.numbers)
        matched_text = ", ".join(str(number) for number in matched_numbers) if matched_numbers else "없음"
        bonus_matched = winning.bonus in ticket.numbers
        bonus_text = " 보너스 일치." if bonus_matched else ""
        detail_header = f"로또 {round_no}회 당첨번호 {format_lotto_numbers(winning.numbers)} + {winning.bonus}"
        if match.rank:
            amount = f"{match.amount:,}원" if match.amount is not None else "당첨금 확인 필요"
            result_label = f"{match.rank}등 {amount}"
            text = (
                f"{label}. {result_label}. "
                f"일치 {match.matched_count}개. 내 번호 {selected}. 당첨번호 {winning_text}."
            )
            detail_text = f"{short_label}. {result_label}. 맞은 번호 {matched_text}.{bonus_text}"
        else:
            result_label = "미당첨"
            text = (
                f"{label}. 미당첨. 일치 {match.matched_count}개. "
                f"내 번호 {selected}. 당첨번호 {winning_text}."
            )
            detail_text = f"{short_label}. 미당첨. 맞은 번호 {matched_text}.{bonus_text}"
        yield Outcome(
            "lotto",
            round_no,
            label,
            text,
            fingerprint,
            True,
            won=match.is_winner,
            result_label=result_label,
            match_count=match.matched_count,
            summary_text=f"{short_label} {result_label}",
            detail_header=detail_header,
            detail_text=detail_text,
        )


def _pension_outcomes(tickets: Iterable[PensionTicket], salt: str) -> Iterable[Outcome]:
    latest_round: int | None = None
    winning_cache = {}
    for ticket in tickets:
        round_no = _resolve_round(ticket.round, latest_round, fetch_latest_pension_round)
        if ticket.round == "latest":
            latest_round = round_no
        fingerprint = fingerprint_ticket({**ticket.state_payload(), "round": round_no}, salt)
        label = ticket.label or f"연금복권 {round_no}회"
        try:
            if round_no not in winning_cache:
                winning_cache[round_no] = fetch_pension_winning(round_no)
            winning = winning_cache[round_no]
            matches = check_pension(ticket.group, ticket.number, winning)
        except PensionResultNotReady as exc:
            yield Outcome("pension", round_no, label, f"{label}. 결과 대기 중입니다. {exc}", fingerprint, False)
            continue

        selected = f"{ticket.group}조 {ticket.number}"
        winning_text = f"{winning.group}조 {winning.number}, 보너스 각조 {winning.bonus_number}"
        short_label = _short_label(label, "pension", round_no)
        detail_header = f"연금복권 {round_no}회 당첨번호 {winning_text}"
        if matches:
            result_text = ", ".join(f"{match.rank_label} {match.amount_label}" for match in matches)
            text = f"{label}. {result_text}. 내 번호 {selected}. 당첨번호 {winning_text}."
        else:
            result_text = "미당첨"
            text = f"{label}. 미당첨. 내 번호 {selected}. 당첨번호 {winning_text}."
        yield Outcome(
            "pension",
            round_no,
            label,
            text,
            fingerprint,
            True,
            won=bool(matches),
            result_label=result_text,
            summary_text=f"{short_label} {result_text}",
            detail_header=detail_header,
            detail_text=f"{short_label}. {result_text}. 내 번호 {selected}.",
        )


def _resolve_round(round_value: int | str, cached_latest: int | None, loader) -> int:
    if round_value == "latest":
        return cached_latest if cached_latest is not None else int(loader())
    return int(round_value)


def _format_messages(unsent: list[Outcome], all_outcomes: list[Outcome]) -> list[str]:
    if unsent:
        return [_format_summary_message(unsent), _format_detail_message(unsent)]

    pending = [outcome.text for outcome in all_outcomes if not outcome.resolved]
    if pending:
        return ["\n".join(["동행복권 결과 상세", *pending])]
    return ["동행복권 결과 요약\n새로 알릴 결과가 없습니다."]


def _format_report(unsent: list[Outcome], all_outcomes: list[Outcome]) -> str:
    return "\n\n".join(_format_messages(unsent, all_outcomes))


def _format_summary_message(outcomes: list[Outcome]) -> str:
    lines = ["동행복권 결과 요약"]
    for group in _group_outcomes(outcomes):
        won_count = sum(1 for outcome in group if outcome.won)
        losing_count = len(group) - won_count
        lines.append(f"{_group_title(group[0])}. {len(group)}게임 중 당첨 {won_count}개, 미당첨 {losing_count}개.")
        if won_count:
            lines.extend(outcome.summary_text or f"{outcome.label} {outcome.result_label}" for outcome in group if outcome.won)
            continue
        match_counts = [outcome.match_count for outcome in group if outcome.match_count is not None]
        if match_counts:
            lines.append(f"최고 일치 {max(match_counts)}개. 이번 회차는 당첨 없음.")
        else:
            lines.append("이번 회차는 당첨 없음.")
    return "\n".join(lines)


def _format_detail_message(outcomes: list[Outcome]) -> str:
    lines = ["동행복권 결과 상세"]
    shown_rules: set[tuple[str, int]] = set()
    current_header = ""
    for outcome in outcomes:
        if outcome.detail_header and outcome.detail_header != current_header:
            lines.append(outcome.detail_header)
            current_header = outcome.detail_header
        rule_key = (outcome.game, outcome.round)
        if outcome.game == "lotto" and rule_key not in shown_rules:
            lines.append("로또는 3개부터 당첨입니다.")
            shown_rules.add(rule_key)
        lines.append(outcome.detail_text or outcome.text)
    return "\n".join(lines)


def _group_outcomes(outcomes: list[Outcome]) -> list[list[Outcome]]:
    groups: list[list[Outcome]] = []
    indexes: dict[tuple[str, int], int] = {}
    for outcome in outcomes:
        key = (outcome.game, outcome.round)
        if key not in indexes:
            indexes[key] = len(groups)
            groups.append([])
        groups[indexes[key]].append(outcome)
    return groups


def _group_title(outcome: Outcome) -> str:
    if outcome.game == "lotto":
        return f"로또 {outcome.round}회"
    if outcome.game == "pension":
        return f"연금복권 {outcome.round}회"
    return f"{outcome.game} {outcome.round}회"


def _short_label(label: str, game: str, round_no: int) -> str:
    prefixes = []
    if game == "lotto":
        prefixes.append(f"로또 {round_no}회 ")
    if game == "pension":
        prefixes.append(f"연금복권 {round_no}회 ")
    for prefix in prefixes:
        if label.startswith(prefix):
            return label[len(prefix):]
    return label
