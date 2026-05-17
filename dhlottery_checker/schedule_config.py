# 카카오 알림 시간 설정을 읽고 실행 대상 시간을 판정하는 모듈
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, time, timedelta
import json
from pathlib import Path
import sys
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


DEFAULT_SETTINGS_PATH = "data/notification-settings.yml"
DEFAULT_TIMEZONE = "Asia/Seoul"
DEFAULT_WINDOW_MINUTES = 30


DAY_INDEXES = {
    "monday": 0,
    "mon": 0,
    "월요일": 0,
    "월": 0,
    "tuesday": 1,
    "tue": 1,
    "화요일": 1,
    "화": 1,
    "wednesday": 2,
    "wed": 2,
    "수요일": 2,
    "수": 2,
    "thursday": 3,
    "thu": 3,
    "목요일": 3,
    "목": 3,
    "friday": 4,
    "fri": 4,
    "금요일": 4,
    "금": 4,
    "saturday": 5,
    "sat": 5,
    "토요일": 5,
    "토": 5,
    "sunday": 6,
    "sun": 6,
    "일요일": 6,
    "일": 6,
}


DEFAULT_GAME_SETTINGS = {
    "lotto": {"enabled": True, "day": "saturday", "time": "21:45"},
    "pension": {"enabled": True, "day": "thursday", "time": "20:10"},
}


@dataclass(frozen=True)
class GameNotificationSchedule:
    game: str
    enabled: bool
    day: str
    day_index: int
    time_text: str
    time_value: time


@dataclass(frozen=True)
class NotificationSchedule:
    timezone: str
    window_minutes: int
    games: tuple[GameNotificationSchedule, ...]


@dataclass(frozen=True)
class NotificationDecision:
    should_run: bool
    reason: str
    due_games: tuple[str, ...]
    local_time: datetime
    schedule: NotificationSchedule


def load_notification_schedule(path: str | Path = DEFAULT_SETTINGS_PATH) -> NotificationSchedule:
    settings_path = Path(path)
    raw_schedule = _read_schedule_source(settings_path) if settings_path.exists() else {}

    timezone_name = str(raw_schedule.get("timezone", DEFAULT_TIMEZONE)).strip() or DEFAULT_TIMEZONE
    try:
        ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"알 수 없는 timezone입니다. {timezone_name}") from exc

    window_minutes = _parse_window_minutes(raw_schedule.get("window_minutes", DEFAULT_WINDOW_MINUTES))
    games = tuple(_parse_game_schedule(raw_schedule, game) for game in DEFAULT_GAME_SETTINGS)
    return NotificationSchedule(
        timezone=timezone_name,
        window_minutes=window_minutes,
        games=games,
    )


def decide_notification_schedule(
    path: str | Path = DEFAULT_SETTINGS_PATH,
    *,
    now: datetime | None = None,
    event_name: str = "schedule",
    force_notify: bool = False,
) -> NotificationDecision:
    schedule = load_notification_schedule(path)
    local_time = _local_datetime(schedule.timezone, now)

    if force_notify:
        return NotificationDecision(True, "force_notify", tuple(game.game for game in schedule.games), local_time, schedule)
    if event_name != "schedule":
        return NotificationDecision(True, "manual_dispatch", tuple(game.game for game in schedule.games), local_time, schedule)

    due_games = tuple(game.game for game in schedule.games if _is_game_due(game, local_time, schedule.window_minutes))
    return NotificationDecision(
        should_run=bool(due_games),
        reason="scheduled_window" if due_games else "outside_schedule",
        due_games=due_games,
        local_time=local_time,
        schedule=schedule,
    )


def decision_payload(decision: NotificationDecision) -> dict[str, Any]:
    return {
        "should_run": decision.should_run,
        "reason": decision.reason,
        "due_games": list(decision.due_games),
        "local_time": decision.local_time.isoformat(),
        "timezone": decision.schedule.timezone,
        "window_minutes": decision.schedule.window_minutes,
    }


def write_github_output(path: str | Path, decision: NotificationDecision) -> None:
    output_path = Path(path)
    with output_path.open("a", encoding="utf-8") as output:
        output.write(f"should_run={str(decision.should_run).lower()}\n")
        output.write(f"reason={decision.reason}\n")
        output.write(f"due_games={','.join(decision.due_games)}\n")
        output.write(f"local_time={decision.local_time.isoformat()}\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="저장된 카카오 알림 시간 기준으로 지금 검사할지 판단합니다.")
    parser.add_argument("--settings", default=DEFAULT_SETTINGS_PATH, help="카카오 알림 시간 YAML 파일 경로입니다.")
    parser.add_argument("--event-name", default="schedule", help="GitHub Actions 이벤트 이름입니다.")
    parser.add_argument("--force-notify", action="store_true", help="저장된 시간과 무관하게 이번 실행을 통과시킵니다.")
    parser.add_argument("--github-output", help="GitHub Actions output 파일 경로입니다.")
    args = parser.parse_args(argv)

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


def _read_schedule_source(path: Path) -> dict[str, Any]:
    source: dict[str, Any] = {}
    section = ""
    section_indent = -1

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        stripped = line.strip()
        if not stripped:
            continue
        indent = len(line) - len(line.lstrip(" "))

        if stripped == "notification_schedule:":
            section = ""
            section_indent = -1
            continue

        if section and indent <= section_indent:
            section = ""
            section_indent = -1

        if stripped in ("lotto:", "pension:"):
            section = stripped[:-1]
            section_indent = indent
            source.setdefault(section, {})
            continue

        key, value = _split_assignment(stripped)
        if not key:
            continue
        if section:
            game_source = source.setdefault(section, {})
            if not isinstance(game_source, dict):
                raise ValueError(f"{section} 알림 설정은 YAML 객체여야 합니다.")
            game_source[key] = _clean_scalar(value)
        else:
            source[key] = _clean_scalar(value)

    return source


def _split_assignment(value: str) -> tuple[str, str]:
    if ":" not in value:
        return "", ""
    key, raw_value = value.split(":", 1)
    return key.strip(), raw_value.strip()


def _clean_scalar(value: str) -> str:
    return value.strip().strip("\"'")


def _parse_game_schedule(raw_schedule: dict[str, Any], game: str) -> GameNotificationSchedule:
    defaults = DEFAULT_GAME_SETTINGS[game]
    raw_game = raw_schedule.get(game, {})
    if raw_game is None:
        raw_game = {}
    if not isinstance(raw_game, dict):
        raise ValueError(f"{game} 알림 설정은 YAML 객체여야 합니다.")

    enabled = _parse_bool(raw_game.get("enabled", defaults["enabled"]))
    day = str(raw_game.get("day", defaults["day"])).strip().lower()
    if day not in DAY_INDEXES:
        raise ValueError(f"{game}.day 값이 올바르지 않습니다. {day}")
    time_text, time_value = _parse_time(raw_game.get("time", defaults["time"]), game)
    return GameNotificationSchedule(
        game=game,
        enabled=enabled,
        day=day,
        day_index=DAY_INDEXES[day],
        time_text=time_text,
        time_value=time_value,
    )


def _parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in ("true", "yes", "y", "1", "on"):
            return True
        if lowered in ("false", "no", "n", "0", "off"):
            return False
    raise ValueError("enabled 값은 true 또는 false여야 합니다.")


def _parse_time(value: Any, game: str) -> tuple[str, time]:
    if not isinstance(value, str):
        raise ValueError(f"{game}.time 값은 HH:MM 문자열이어야 합니다.")
    parts = value.strip().split(":")
    if len(parts) != 2:
        raise ValueError(f"{game}.time 값은 HH:MM 형식이어야 합니다.")
    try:
        hour = int(parts[0])
        minute = int(parts[1])
        parsed = time(hour=hour, minute=minute)
    except ValueError as exc:
        raise ValueError(f"{game}.time 값은 HH:MM 형식이어야 합니다.") from exc
    return f"{hour:02d}:{minute:02d}", parsed


def _parse_window_minutes(value: Any) -> int:
    try:
        minutes = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("window_minutes 값은 숫자여야 합니다.") from exc
    if minutes < 1 or minutes > 360:
        raise ValueError("window_minutes 값은 1부터 360 사이여야 합니다.")
    return minutes


def _local_datetime(timezone_name: str, now: datetime | None) -> datetime:
    timezone = ZoneInfo(timezone_name)
    if now is None:
        return datetime.now(timezone)
    if now.tzinfo is None:
        return now.replace(tzinfo=timezone)
    return now.astimezone(timezone)


def _is_game_due(game: GameNotificationSchedule, local_time: datetime, window_minutes: int) -> bool:
    if not game.enabled:
        return False
    if local_time.weekday() != game.day_index:
        return False
    starts_at = local_time.replace(
        hour=game.time_value.hour,
        minute=game.time_value.minute,
        second=0,
        microsecond=0,
    )
    return starts_at <= local_time < starts_at + timedelta(minutes=window_minutes)


if __name__ == "__main__":
    raise SystemExit(main())
