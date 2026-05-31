# 당첨 확인 결과를 알림과 CLI 출력 문구로 포맷하는 모듈
from __future__ import annotations

from .lotto import LOTTO_RESULT_PAGE
from .outcome import Outcome, group_outcomes, group_title


PENSION_RESULT_PAGE = "https://www.dhlottery.co.kr/pt720/result"


def format_messages(unsent: list[Outcome], all_outcomes: list[Outcome]) -> list[str]:
    messages = []
    if unsent:
        messages.extend([format_summary_message(unsent), format_detail_message(unsent)])

    pending = [outcome for outcome in all_outcomes if not outcome.resolved]
    if pending:
        messages.append(format_pending_message(pending))
    if messages:
        return messages
    return ["[동행복권 결과 요약]\n새로 알릴 결과가 없습니다."]


def format_report(unsent: list[Outcome], all_outcomes: list[Outcome]) -> str:
    return "\n\n".join(format_messages(unsent, all_outcomes))


def format_summary_message(outcomes: list[Outcome]) -> str:
    lines = ["[동행복권 결과 요약]"]
    groups = group_outcomes(outcomes)
    winning_lines = []
    for group in groups:
        won_count = sum(1 for outcome in group if outcome.won)
        losing_count = len(group) - won_count
        lines.append(f"{group_title(group[0])}. 당첨 {won_count}개, 미당첨 {losing_count}개.")
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


def format_detail_message(outcomes: list[Outcome]) -> str:
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


def format_pending_message(outcomes: list[Outcome]) -> str:
    groups = group_outcomes(outcomes)
    lines = ["[동행복권 결과 요약]"]
    for group in groups:
        if any(is_result_not_ready(outcome) for outcome in group):
            lines.append(f"{group_title(group[0])}. 아직 당첨결과 발표 전입니다.")
        else:
            lines.append(f"{group_title(group[0])}. 결과 조회 실패. 다음 실행에서 다시 시도합니다.")
    lines.append("")
    lines.extend(_result_link_lines(groups))
    if any(is_result_not_ready(outcome) for outcome in outcomes):
        lines.append("")
        lines.append("발표 후 다시 검사하면 당첨 여부를 알려드립니다.")
    return "\n".join(lines)


def is_result_not_ready(outcome: Outcome) -> bool:
    return "결과 대기 중입니다" in outcome.text


def _result_link_lines(groups: list[list[Outcome]]) -> list[str]:
    lines = []
    for group in groups:
        representative = group[0]
        if representative.game == "lotto":
            lines.append(f"{group_title(representative)} {LOTTO_RESULT_PAGE}")
        elif representative.game == "pension":
            lines.append(f"{group_title(representative)} {PENSION_RESULT_PAGE}")
    return lines
