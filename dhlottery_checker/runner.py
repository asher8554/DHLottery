# 구매번호를 당첨번호와 비교하고 알림 흐름을 실행하는 모듈
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path
import sys
from typing import Iterable

from .account import (
    DEFAULT_BALANCE_THRESHOLD,
    DEFAULT_CHARGE_AMOUNT,
    balance_state_payload,
    format_balance_alert,
    load_account_snapshot,
    needs_balance_charge,
)
from .config import LottoTicket, PensionTicket, load_ticket_config
from .http import HttpError, HttpTimeoutError
from .kakao import send_kakao_text
from .lotto import (
    LOTTO_RESULT_PAGE,
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
from .schedule_config import DEFAULT_SETTINGS_PATH, decide_notification_schedule, decision_payload, write_github_output
from .state import SentState, fingerprint_ticket
from .ticket_import import parse_lotto_ticket_text, write_lotto_tickets


PENSION_RESULT_PAGE = "https://www.dhlottery.co.kr/pt720/result"


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
    check_parser.add_argument("--status-json", help="이번 검사 실행 요약을 JSON 파일로 저장합니다.")

    import_parser = subparsers.add_parser("import-ticket", help="동행복권 티켓 보기 텍스트를 구매번호 YAML에 저장합니다.")
    import_parser.add_argument("--input", help="붙여넣기 텍스트 파일 경로입니다. 생략하면 표준 입력을 읽습니다.")
    import_parser.add_argument("--tickets", default="data/tickets.yml", help="갱신할 구매번호 YAML 파일 경로입니다.")
    import_parser.add_argument("--replace-all", action="store_true", help="기존 설정을 모두 지우고 가져온 로또 항목만 저장합니다.")
    import_parser.add_argument("--replace-lotto", action="store_true", help="기존 로또 항목을 지우고 가져온 항목만 저장합니다.")

    scrape_parser = subparsers.add_parser("scrape-ledger", help="로컬 브라우저에서 동행복권 구매내역을 가져옵니다.")
    scrape_parser.add_argument("--tickets", default="data/tickets.yml", help="갱신할 구매번호 YAML 파일 경로입니다.")
    scrape_parser.add_argument("--account", default="data/account.yml", help="갱신할 예치금 YAML 파일 경로입니다.")
    scrape_parser.add_argument("--profile-dir", default=".browser/dhlottery", help="로그인 세션을 보관할 로컬 브라우저 프로필 경로입니다.")
    scrape_parser.add_argument("--env-file", default=".env", help="동행복권 로그인용 로컬 env 파일 경로입니다.")
    scrape_parser.add_argument("--login-url", default="https://www.dhlottery.co.kr/login", help="자동 로그인에 사용할 동행복권 로그인 페이지입니다.")
    scrape_parser.add_argument("--main-url", default="https://www.dhlottery.co.kr/main", help="예치금을 읽을 동행복권 메인 페이지입니다.")
    scrape_parser.add_argument("--max-tickets", type=int, default=30, help="클릭할 티켓 보기 버튼의 최대 개수입니다.")
    scrape_parser.add_argument("--headless", action="store_true", help="브라우저 창을 띄우지 않습니다. 이미 로그인 세션이 있을 때만 사용하세요.")
    scrape_parser.add_argument("--append", action="store_true", help="기존 구매번호를 지우지 않고 새 번호만 추가합니다.")
    scrape_parser.add_argument("--verbose", action="store_true", help="구매내역 수집 진행 상황을 출력합니다.")

    balance_parser = subparsers.add_parser("balance-alert", help="예치금이 기준 이하이면 카카오톡 알림을 보냅니다.")
    balance_parser.add_argument("--account", default="data/account.yml", help="예치금 YAML 파일 경로입니다.")
    balance_parser.add_argument("--threshold", type=int, default=DEFAULT_BALANCE_THRESHOLD, help="알림을 보낼 예치금 기준입니다.")
    balance_parser.add_argument("--charge-amount", type=int, default=DEFAULT_CHARGE_AMOUNT, help="알림에 표시할 권장 충전 금액입니다.")
    balance_parser.add_argument("--notify", action="store_true", help="카카오톡 알림을 보냅니다.")
    balance_parser.add_argument("--dry-run", action="store_true", help="카카오톡 알림 없이 메시지만 출력합니다.")
    balance_parser.add_argument("--state", default=".state/balance-alert.json", help="중복 알림 방지 상태 파일입니다.")
    balance_parser.add_argument("--no-state", action="store_true", help="중복 알림 방지 상태를 사용하지 않습니다.")
    balance_parser.add_argument("--force-notify", action="store_true", help="이미 보낸 예치금 부족 알림도 다시 보냅니다.")

    schedule_parser = subparsers.add_parser("schedule-due", help="저장된 카카오 알림 시간 기준으로 지금 검사할지 판단합니다.")
    schedule_parser.add_argument("--settings", default=DEFAULT_SETTINGS_PATH, help="카카오 알림 시간 YAML 파일 경로입니다.")
    schedule_parser.add_argument("--event-name", default=os.environ.get("GITHUB_EVENT_NAME", "schedule"), help="GitHub Actions 이벤트 이름입니다.")
    schedule_parser.add_argument("--force-notify", action="store_true", help="저장된 시간과 무관하게 이번 실행을 통과시킵니다.")
    schedule_parser.add_argument("--github-output", help="GitHub Actions output 파일 경로입니다.")

    args = parser.parse_args(argv)
    if args.command == "check":
        return _run_check(args)
    if args.command == "import-ticket":
        return _run_import_ticket(args)
    if args.command == "scrape-ledger":
        return _run_scrape_ledger(args)
    if args.command == "balance-alert":
        return _run_balance_alert(args)
    if args.command == "schedule-due":
        return _run_schedule_due(args)
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


def _run_scrape_ledger(args: argparse.Namespace) -> int:
    try:
        from .ledger_scraper import scrape_ledger_to_file

        result = scrape_ledger_to_file(
            ticket_path=args.tickets,
            account_path=args.account,
            profile_dir=args.profile_dir,
            env_file=args.env_file,
            login_url=args.login_url,
            main_url=args.main_url,
            max_tickets=args.max_tickets,
            headless=args.headless,
            append=args.append,
            verbose=args.verbose,
        )
    except (RuntimeError, ValueError) as exc:
        print(f"구매내역 가져오기 실패. {exc}", file=sys.stderr)
        return 2

    message = (
        f"{args.tickets} 파일을 갱신했습니다. "
        f"로또 {len(result.imported_tickets.lotto)}개, "
        f"연금복권 {len(result.imported_tickets.pension)}개를 가져왔습니다."
    )
    if result.balance_amount is None:
        message += " 예치금은 찾지 못했습니다."
    else:
        message += f" 예치금 {result.balance_amount:,}원도 저장했습니다."
    print(message)
    return 0


def _run_balance_alert(args: argparse.Namespace) -> int:
    try:
        snapshot = load_account_snapshot(args.account)
    except ValueError as exc:
        print(f"예치금 확인 실패. {exc}", file=sys.stderr)
        return 2

    message = format_balance_alert(
        snapshot,
        threshold=args.threshold,
        charge_amount=args.charge_amount,
    )
    print(message)

    if not needs_balance_charge(snapshot, args.threshold):
        return 0

    state = None if args.no_state else SentState.load(args.state)
    salt = os.environ.get("STATE_HASH_SALT", "")
    fingerprint = fingerprint_ticket(
        balance_state_payload(
            snapshot,
            threshold=args.threshold,
            charge_amount=args.charge_amount,
        ),
        salt,
    )
    should_notify = args.force_notify or state is None or not state.is_sent(fingerprint)

    if args.notify and not args.dry_run and should_notify:
        send_kakao_text(message)
        if state is not None:
            state.mark_sent(fingerprint, "balance", 0)
            state.save()
    elif state is not None and not Path(args.state).exists():
        state.save()
    return 0


def _run_schedule_due(args: argparse.Namespace) -> int:
    try:
        decision = decide_notification_schedule(
            args.settings,
            event_name=args.event_name,
            force_notify=args.force_notify,
        )
    except ValueError as exc:
        print(f"알림 시간 설정 오류. {exc}", file=sys.stderr)
        return 2

    print(json.dumps(decision_payload(decision), ensure_ascii=False, indent=2))
    if args.github_output:
        write_github_output(args.github_output, decision)
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
    pending = [outcome for outcome in outcomes if not outcome.resolved]
    pending_to_notify = [outcome for outcome in pending if _is_result_not_ready(outcome)]
    sent_resolved_count = 0
    sent_pending_count = 0

    messages = _format_messages(unsent, outcomes)
    notification_messages = _format_messages(unsent, pending_to_notify)
    print("\n\n".join(messages))

    if args.notify and not args.dry_run and (unsent or pending_to_notify):
        for message in notification_messages:
            send_kakao_text(message)
        sent_resolved_count = len(unsent)
        sent_pending_count = len(pending_to_notify)
        if state is not None:
            for outcome in unsent:
                state.mark_sent(outcome.fingerprint, outcome.game, outcome.round)
            state.save()
    elif state is not None and not Path(args.state).exists():
        state.save()

    _write_status_json(
        args.status_json,
        resolved_count=len(resolved),
        unsent_resolved_count=len(unsent),
        pending_count=len(pending),
        pending_not_ready_count=len(pending_to_notify),
        sent_resolved_count=sent_resolved_count,
        sent_pending_count=sent_pending_count,
        clear_tickets=sent_resolved_count > 0 and len(pending) == 0,
    )
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
        try:
            round_no = _resolve_round(ticket.round, latest_round, fetch_latest_lotto_round)
        except (LottoResultNotReady, HttpError) as exc:
            round_no = 0 if ticket.round == "latest" else int(ticket.round)
            label = ticket.label or f"로또 {round_no}회"
            fingerprint = fingerprint_ticket({**ticket.state_payload(), "round": round_no}, salt)
            reason = _pending_reason(exc, LottoResultNotReady)
            yield Outcome("lotto", round_no, label, f"{label}. {reason}. {exc}", fingerprint, False)
            continue
        if ticket.round == "latest":
            latest_round = round_no
        fingerprint = fingerprint_ticket({**ticket.state_payload(), "round": round_no}, salt)
        label = ticket.label or f"로또 {round_no}회"
        try:
            if round_no not in winning_cache:
                winning_cache[round_no] = fetch_lotto_winning(round_no)
            winning = winning_cache[round_no]
            match = check_lotto(ticket.numbers, winning)
        except (LottoResultNotReady, HttpError) as exc:
            reason = _pending_reason(exc, LottoResultNotReady)
            yield Outcome("lotto", round_no, label, f"{label}. {reason}. {exc}", fingerprint, False)
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
        try:
            round_no = _resolve_round(ticket.round, latest_round, fetch_latest_pension_round)
        except (PensionResultNotReady, HttpError) as exc:
            round_no = 0 if ticket.round == "latest" else int(ticket.round)
            label = ticket.label or f"연금복권 {round_no}회"
            fingerprint = fingerprint_ticket({**ticket.state_payload(), "round": round_no}, salt)
            reason = _pending_reason(exc, PensionResultNotReady)
            yield Outcome("pension", round_no, label, f"{label}. {reason}. {exc}", fingerprint, False)
            continue
        if ticket.round == "latest":
            latest_round = round_no
        fingerprint = fingerprint_ticket({**ticket.state_payload(), "round": round_no}, salt)
        label = ticket.label or f"연금복권 {round_no}회"
        try:
            if round_no not in winning_cache:
                winning_cache[round_no] = fetch_pension_winning(round_no)
            winning = winning_cache[round_no]
            matches = check_pension(ticket.group, ticket.number, winning)
        except (PensionResultNotReady, HttpError) as exc:
            reason = _pending_reason(exc, PensionResultNotReady)
            yield Outcome("pension", round_no, label, f"{label}. {reason}. {exc}", fingerprint, False)
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
            summary_text=f"{short_label} {selected} {result_text}",
            detail_header=detail_header,
            detail_text=f"{short_label}. {result_text}. 내 번호 {selected}.",
        )


def _resolve_round(round_value: int | str, cached_latest: int | None, loader) -> int:
    if round_value == "latest":
        return cached_latest if cached_latest is not None else int(loader())
    return int(round_value)


def _format_messages(unsent: list[Outcome], all_outcomes: list[Outcome]) -> list[str]:
    messages = []
    if unsent:
        messages.extend([_format_summary_message(unsent), _format_detail_message(unsent)])

    pending = [outcome for outcome in all_outcomes if not outcome.resolved]
    if pending:
        messages.append(_format_pending_message(pending))
    if messages:
        return messages
    return ["[동행복권 결과 요약]\n새로 알릴 결과가 없습니다."]


def _format_report(unsent: list[Outcome], all_outcomes: list[Outcome]) -> str:
    return "\n\n".join(_format_messages(unsent, all_outcomes))


def _write_status_json(path: str | None, **status: int | bool) -> None:
    if not path:
        return
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _format_summary_message(outcomes: list[Outcome]) -> str:
    lines = ["[동행복권 결과 요약]"]
    groups = _group_outcomes(outcomes)
    winning_lines = []
    for group in groups:
        won_count = sum(1 for outcome in group if outcome.won)
        losing_count = len(group) - won_count
        lines.append(f"{_group_title(group[0])}. 당첨 {won_count}개, 미당첨 {losing_count}개.")
        if won_count:
            winning_text = ", ".join(
                outcome.summary_text or f"{outcome.label} {outcome.result_label}"
                for outcome in group
                if outcome.won
            )
            winning_lines.append(f"당첨. {winning_text}.")
    lines.extend(winning_lines)
    lines.append("")
    lines.extend(_result_link_lines(groups))
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


def _format_pending_message(outcomes: list[Outcome]) -> str:
    groups = _group_outcomes(outcomes)
    lines = ["[동행복권 결과 요약]"]
    for group in groups:
        if any(_is_result_not_ready(outcome) for outcome in group):
            lines.append(f"{_group_title(group[0])}. 아직 당첨결과 발표 전입니다.")
        else:
            lines.append(f"{_group_title(group[0])}. 결과 조회 실패. 다음 실행에서 다시 시도합니다.")
    lines.append("")
    lines.extend(_result_link_lines(groups))
    if any(_is_result_not_ready(outcome) for outcome in outcomes):
        lines.append("")
        lines.append("발표 후 다시 검사하면 당첨 여부를 알려드립니다.")
    return "\n".join(lines)


def _is_result_not_ready(outcome: Outcome) -> bool:
    return "결과 대기 중입니다" in outcome.text


def _pending_reason(exc: Exception, result_not_ready_type: type[Exception]) -> str:
    if isinstance(exc, (result_not_ready_type, HttpTimeoutError)):
        return "결과 대기 중입니다"
    return "결과 조회 실패. 다음 실행에서 다시 시도합니다"


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


def _result_link_lines(groups: list[list[Outcome]]) -> list[str]:
    lines = []
    for group in groups:
        representative = group[0]
        if representative.game == "lotto":
            lines.append(f"{_group_title(representative)} {LOTTO_RESULT_PAGE}")
        elif representative.game == "pension":
            lines.append(f"{_group_title(representative)} {PENSION_RESULT_PAGE}")
    return lines


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
