# 로그인된 로컬 브라우저에서 구매내역 티켓 텍스트를 수집하는 모듈
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import os
from pathlib import Path
import re
from typing import Iterable

from .ticket_import import (
    ImportedLottoTicket,
    ImportedPensionTicket,
    ImportedTickets,
    parse_ticket_text,
    write_imported_tickets,
)


LEDGER_URL = "https://www.dhlottery.co.kr/mypage/mylotteryledger"
LOGIN_URL = "https://www.dhlottery.co.kr/login"
PASSWORD_SELECTORS = (
    "#inpUserPswdEncn",
    "input.login-pw",
    "input[aria-label='비밀번호']",
    "input[placeholder='비밀번호']",
    "input[type='password']",
    "input[name='password']",
    "input[name='passwd']",
    "input[name='userPwd']",
    "#userPwd",
    "#password",
)
USERNAME_SELECTORS = (
    "#inpUserId",
    "input[name='inpUserId']",
    "input.login-id",
    "input[aria-label='아이디']",
    "input[placeholder='아이디']",
    "input[name='userId']",
    "input[name='userID']",
    "input[name='loginId']",
    "input[name='id']",
    "#userId",
    "#loginId",
    "input[type='text']",
)
LOGIN_SUBMIT_SELECTORS = (
    "#btnLogin",
    "button.login-btn",
    "button.item-submit",
    "button:has-text('로그인')",
    "input[type='submit']",
    "input[type='button'][value*='로그인']",
    "a:has-text('로그인')",
)
TICKET_BUTTON_PATTERN = re.compile(
    r"(티켓\s*보기|티켓보기|복권\s*보기|복권보기|복권\s*번호\s*보기|번호\s*보기|상세\s*보기|상세보기)"
)
DETAIL_ICON_PATTERN = re.compile(
    r"(돋보기|조회|search|magnifier|btn[-_ ]?search|ico[-_ ]?search|icon[-_ ]?search|btn[-_ ]?view|detail|popup)",
    re.IGNORECASE,
)
BARCODE_BUTTON_PATTERN = re.compile(r"(^|\s)(barcd|col-num)(\s|$)", re.IGNORECASE)
TICKET_CONTEXT_PATTERN = re.compile(
    r"(로또|Lotto|연금복권|구매번호|구입일자|추첨일자|\d\s*조\s*\d{6}|\d{5}\s+\d{5}\s+\d{5})",
    re.IGNORECASE,
)
LEDGER_TICKET_ROW_PATTERN = re.compile(
    r"((로또|Lotto|연금복권).*(구입일자|추첨일자))|(\d\s*조\s*\d{6})|(\d{5}\s+\d{5}\s+\d{5})",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ScrapeLedgerResult:
    imported_tickets: ImportedTickets
    ticket_text_count: int


def scrape_ledger_to_file(
    *,
    ticket_path: str | Path = "data/tickets.yml",
    profile_dir: str | Path = ".browser/dhlottery",
    env_file: str | Path = ".env",
    login_url: str = LOGIN_URL,
    ledger_url: str = LEDGER_URL,
    max_tickets: int = 30,
    headless: bool = False,
    append: bool = False,
    verbose: bool = False,
) -> ScrapeLedgerResult:
    ticket_texts = scrape_ledger_ticket_texts(
        profile_dir=profile_dir,
        env_file=env_file,
        login_url=login_url,
        ledger_url=ledger_url,
        max_tickets=max_tickets,
        headless=headless,
        verbose=verbose,
    )
    imported_tickets = _parse_ticket_texts(ticket_texts)
    write_imported_tickets(ticket_path, imported_tickets, replace_all=not append)
    _log(
        verbose,
        f"{ticket_path} 저장 완료. 로또 {len(imported_tickets.lotto)}개, 연금복권 {len(imported_tickets.pension)}개.",
    )
    return ScrapeLedgerResult(imported_tickets, len(ticket_texts))


def scrape_ledger_ticket_texts(
    *,
    profile_dir: str | Path = ".browser/dhlottery",
    env_file: str | Path = ".env",
    login_url: str = LOGIN_URL,
    ledger_url: str = LEDGER_URL,
    max_tickets: int = 30,
    headless: bool = False,
    verbose: bool = False,
) -> list[str]:
    try:
        from playwright.sync_api import Error as PlaywrightError
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
        from playwright.sync_api import sync_playwright
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Playwright가 설치되어 있지 않습니다. "
            "`python -m pip install -r requirements.txt` 실행 후 "
            "`python -m playwright install chromium`을 한 번 실행하세요."
        ) from exc

    profile_path = Path(profile_dir)
    profile_path.mkdir(parents=True, exist_ok=True)
    credentials = load_dhlottery_credentials(env_file)
    _log(verbose, f"브라우저 프로필 사용. {profile_path}")

    with sync_playwright() as playwright:
        _log(verbose, "브라우저 실행 중.")
        context = playwright.chromium.launch_persistent_context(
            user_data_dir=str(profile_path),
            headless=headless,
            viewport={"width": 1280, "height": 900},
            locale="ko-KR",
        )
        try:
            page = context.pages[0] if context.pages else context.new_page()
            if not headless:
                _log(verbose, f"로그인 페이지 이동. {login_url}")
                _goto_with_navigation_retry(page, login_url, PlaywrightError, PlaywrightTimeoutError)
                if _auto_login_if_possible(page, credentials, PlaywrightTimeoutError):
                    _log(verbose, "로그인 폼 자동 제출 완료.")
                else:
                    _log(verbose, "자동 제출할 로그인 폼을 찾지 못했거나 비밀번호가 없습니다.")
                _wait_for_page_settle(page, PlaywrightTimeoutError)
            _log(verbose, f"구매/당첨내역 이동. {ledger_url}")
            _goto_with_navigation_retry(page, ledger_url, PlaywrightError, PlaywrightTimeoutError)
            if _auto_login_if_possible(page, credentials, PlaywrightTimeoutError):
                _log(verbose, "구매내역 이동 후 로그인 폼을 다시 제출했습니다.")
                _goto_with_navigation_retry(page, ledger_url, PlaywrightError, PlaywrightTimeoutError)
            if not headless and _page_has_login_form(page):
                print("자동 로그인이 되지 않았습니다. 브라우저에서 로그인하고 구매/당첨내역 페이지가 보이면 Enter를 누르세요.")
                input()
                _wait_for_page_settle(page, PlaywrightTimeoutError)
                _goto_with_navigation_retry(page, ledger_url, PlaywrightError, PlaywrightTimeoutError)
            _log(verbose, _ledger_list_summary(_all_body_texts(page)))
            texts = _collect_ticket_texts(context, page, max_tickets, PlaywrightTimeoutError, verbose=verbose)
            if not texts:
                debug_path = _write_debug_snapshot(page, profile_path)
                raise ValueError(
                    "구매내역에서 로또 또는 연금복권 티켓 번호를 찾지 못했습니다. "
                    f"현재 화면 텍스트를 {debug_path}에 저장했습니다. "
                    f"버튼 후보 정보는 {debug_path.with_name('ledger-candidates.txt')}에 저장했습니다."
                )
            _log(verbose, f"상세 텍스트 {len(texts)}개 수집 완료.")
            return texts
        finally:
            _log(verbose, "브라우저 종료.")
            context.close()


def load_dhlottery_credentials(env_file: str | Path = ".env") -> tuple[str, str]:
    values = _load_env_values(env_file)
    username = _first_env_value(values, "DHLOTTERY_ID", "DHLOTTERY_USERNAME", "DHLOTTERY_USER")
    password = _first_env_value(values, "DHLOTTERY_PASSWORD", "DHLOTTERY_PW")
    return username, password


def _load_env_values(env_file: str | Path) -> dict[str, str]:
    values = dict(os.environ)
    path = Path(env_file)
    if not path.exists():
        return values
    values.update(_parse_env_text(path.read_text(encoding="utf-8")))
    return values


def _parse_env_text(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'\"")
        if key:
            values[key] = value
    return values


def _first_env_value(values: dict[str, str], *names: str) -> str:
    for name in names:
        value = values.get(name, "").strip()
        if value:
            return value
    return ""


def _auto_login_if_possible(page, credentials: tuple[str, str], timeout_error_type: type[Exception]) -> bool:
    username, password = credentials
    if not password:
        return False

    password_input = _first_visible_locator(page, PASSWORD_SELECTORS)
    if password_input is None:
        return False

    username_input = _first_visible_locator(page, USERNAME_SELECTORS)
    if username and username_input is not None:
        _fill_input(username_input, username)
    _fill_input(password_input, password)
    _submit_login_form(page, password_input)
    _wait_for_page_settle(page, timeout_error_type)
    return True


def _page_has_login_form(page) -> bool:
    return _first_visible_locator(page, PASSWORD_SELECTORS) is not None


def _first_visible_locator(page, selectors: Iterable[str]):
    for selector in selectors:
        for scope in _locator_scopes(page):
            try:
                locator = scope.locator(selector)
                count = locator.count()
            except Exception:
                continue
            for index in range(count):
                try:
                    candidate = locator.nth(index)
                    if candidate.is_visible(timeout=1000):
                        return candidate
                except Exception:
                    continue
    return None


def _locator_scopes(page):
    frames = getattr(page, "frames", None)
    return frames if frames else (page,)


def _fill_input(locator, value: str) -> None:
    locator.fill(value, timeout=3000)
    for event_name in ("input", "change"):
        try:
            locator.dispatch_event(event_name, timeout=1000)
        except Exception:
            pass


def _submit_login_form(page, password_input) -> None:
    submit_button = _first_visible_locator(page, LOGIN_SUBMIT_SELECTORS)
    if submit_button is not None:
        submit_button.click(timeout=3000)
        return
    password_input.press("Enter", timeout=3000)


def _goto_with_navigation_retry(page, url: str, error_type: type[Exception], timeout_error_type: type[Exception]) -> None:
    last_error: Exception | None = None
    for _ in range(3):
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            _wait_for_page_settle(page, timeout_error_type)
            return
        except error_type as exc:
            last_error = exc
            if not _is_navigation_interruption(exc):
                raise
            _wait_for_page_settle(page, timeout_error_type)
    raise RuntimeError("구매/당첨내역 페이지 이동이 로그인 리다이렉트와 계속 충돌했습니다. 잠시 후 다시 실행하세요.") from last_error


def _wait_for_page_settle(page, timeout_error_type: type[Exception]) -> None:
    for state in ("domcontentloaded", "networkidle"):
        try:
            page.wait_for_load_state(state, timeout=10000)
        except timeout_error_type:
            pass
    try:
        page.wait_for_timeout(1000)
    except Exception:
        pass


def _is_navigation_interruption(exc: Exception) -> bool:
    message = str(exc)
    return "interrupted by another navigation" in message or (
        "Navigation to" in message and "is interrupted" in message
    )


def _collect_ticket_texts(
    context,
    page,
    max_tickets: int,
    timeout_error_type: type[Exception],
    *,
    verbose: bool = False,
) -> list[str]:
    texts: list[str] = []
    buttons = _ticket_button_handles(page)
    _log(verbose, f"상세 버튼 후보 {len(buttons)}개 발견. 최대 {max_tickets}개 확인.")
    for index, handle in enumerate(buttons[:max_tickets], start=1):
        _log(verbose, f"상세 버튼 {index}/{min(len(buttons), max_tickets)} 클릭 중.")
        try:
            text = _text_after_click(context, page, handle, timeout_error_type)
        except Exception as exc:
            _log(verbose, f"상세 버튼 {index} 클릭 실패. {exc}")
            continue
        normalized = _normalize_text(text)
        if normalized and _looks_like_ticket_text(normalized):
            texts.append(normalized)
            _log(verbose, f"상세 버튼 {index}에서 티켓 텍스트 감지.")
        else:
            _log(verbose, f"상세 버튼 {index}에서 티켓 텍스트를 찾지 못했습니다.")

    if not texts:
        for body_text in _all_body_texts(page):
            if _looks_like_ticket_text(body_text):
                texts.append(_normalize_text(body_text))
    return _unique_texts(texts)


def _write_debug_snapshot(page, profile_path: Path) -> Path:
    debug_dir = profile_path.parent / "debug"
    debug_dir.mkdir(parents=True, exist_ok=True)
    text_path = debug_dir / "ledger-body.txt"
    text_path.write_text("\n\n--- frame ---\n\n".join(_all_body_texts(page)), encoding="utf-8")
    candidate_path = debug_dir / "ledger-candidates.txt"
    candidate_path.write_text("\n\n".join(_ticket_button_debug_labels(page)), encoding="utf-8")
    try:
        page.screenshot(path=str(debug_dir / "ledger-page.png"), full_page=True)
    except Exception:
        pass
    return text_path


def _ticket_button_handles(page) -> list[object]:
    ticket_handles = []
    for frame in page.frames:
        handles = frame.query_selector_all(
            "a, button, input[type='button'], input[type='submit'], img, area, .barcd, [role='button'], [onclick]"
        )
        for handle in handles:
            try:
                label = _ticket_button_label(handle)
            except Exception:
                continue
            if _is_ticket_button_candidate(label.get("own", ""), label.get("context", "")):
                ticket_handles.append(handle)
    return ticket_handles


def is_ticket_button_label(label: str) -> bool:
    normalized = _normalize_text(label)
    return (
        TICKET_BUTTON_PATTERN.search(normalized) is not None
        or LEDGER_TICKET_ROW_PATTERN.search(normalized) is not None
    ) or (
        DETAIL_ICON_PATTERN.search(normalized) is not None
        and TICKET_CONTEXT_PATTERN.search(normalized) is not None
    )


def _is_ticket_button_candidate(own_label: str, context_label: str) -> bool:
    own = _normalize_text(own_label)
    context = _normalize_text(context_label)
    has_ticket_button_marker = (
        TICKET_BUTTON_PATTERN.search(own) is not None
        or DETAIL_ICON_PATTERN.search(own) is not None
        or BARCODE_BUTTON_PATTERN.search(own) is not None
    )
    return has_ticket_button_marker and LEDGER_TICKET_ROW_PATTERN.search(context) is not None


def _ticket_button_label(handle) -> dict[str, str]:
    return handle.evaluate(
        """
        (el) => {
          const ownParts = [];
          const contextParts = [];
          const childImageLabels = Array.from(el.querySelectorAll?.('img') ?? [])
            .flatMap((img) => [
              img.getAttribute('alt'),
              img.getAttribute('title'),
              img.getAttribute('src')
            ]);
          ownParts.push(
            el.innerText,
            el.textContent,
            el.value,
            el.getAttribute('aria-label'),
            el.getAttribute('title'),
            el.getAttribute('alt'),
            el.getAttribute('onclick'),
            el.getAttribute('href'),
            el.id,
            el.className,
            ...childImageLabels
          );

          let ancestor = el.parentElement;
          for (let depth = 0; ancestor && depth < 4; depth += 1) {
            contextParts.push(ancestor.innerText, ancestor.className, ancestor.id);
            ancestor = ancestor.parentElement;
          }

          return {
            own: ownParts.filter(Boolean).join(' '),
            context: contextParts.filter(Boolean).join(' ')
          };
        }
        """
    )


def _ticket_button_debug_labels(page) -> list[str]:
    debug_labels = []
    for frame_index, frame in enumerate(page.frames):
        try:
            handles = frame.query_selector_all(
                "a, button, input[type='button'], input[type='submit'], img, area, .barcd, [role='button'], [onclick]"
            )
        except Exception:
            continue
        for index, handle in enumerate(handles):
            try:
                label = _ticket_button_label(handle)
            except Exception as exc:
                debug_labels.append(f"frame={frame_index} index={index} error={exc}")
                continue
            own = _normalize_text(label.get("own", ""))[:500]
            context = _normalize_text(label.get("context", ""))[:1000]
            matched = _is_ticket_button_candidate(label.get("own", ""), label.get("context", ""))
            debug_labels.append(f"frame={frame_index} index={index} matched={matched}\nown={own}\ncontext={context}")
    return debug_labels


def _text_after_click(context, page, handle, timeout_error_type: type[Exception]) -> str:
    popup = None
    before_texts = _all_body_texts(page)
    try:
        with context.expect_page(timeout=4000) as popup_info:
            handle.click(timeout=5000)
        popup = popup_info.value
        _wait_for_page_settle(popup, timeout_error_type)
        return "\n".join(_all_body_texts(popup))
    except timeout_error_type:
        page.wait_for_timeout(1000)
        text = _visible_ticket_popup_text(page)
        after_texts = _all_body_texts(page)
        if not text:
            text = _text_added_after_click(before_texts, after_texts)
        if not _looks_like_ticket_text(text):
            text = "\n".join(after_texts)
        _close_dialog(page)
        return text
    finally:
        if popup is not None:
            popup.close()


def _all_body_texts(page) -> list[str]:
    texts = []
    for frame in page.frames:
        try:
            text = frame.locator("body").inner_text(timeout=5000)
        except Exception:
            continue
        normalized = _normalize_text(text)
        if normalized:
            texts.append(normalized)
    return texts


def _text_added_after_click(before_texts: Iterable[str], after_texts: Iterable[str]) -> str:
    before_lines = Counter(_split_text_lines("\n".join(before_texts)))
    added_lines = []
    for line in _split_text_lines("\n".join(after_texts)):
        if before_lines[line] > 0:
            before_lines[line] -= 1
            continue
        added_lines.append(line)
    return "\n".join(added_lines)


def _visible_ticket_popup_text(page) -> str:
    selectors = (
        "#Lotto645TicketP",
        "#Pension720TicketP",
        ".popup-wrap.on",
        "[id*='TicketP']",
        "[class*='popup-wrap']",
    )
    for frame in page.frames:
        for selector in selectors:
            try:
                locator = frame.locator(selector)
                count = locator.count()
            except Exception:
                continue
            for index in range(count):
                candidate = locator.nth(index)
                try:
                    if not candidate.is_visible(timeout=500):
                        continue
                    text = candidate.inner_text(timeout=1000)
                except Exception:
                    continue
                normalized = _normalize_text(text)
                if _looks_like_ticket_text(normalized):
                    return normalized
    return ""


def _split_text_lines(text: str) -> list[str]:
    return [line for line in _normalize_text(text).split("\n") if line.strip()]


def _ledger_list_summary(texts: Iterable[str]) -> str:
    text = "\n".join(texts)
    pension_count = len(re.findall(r"연금복권720\+\s*\n?\s*\d{1,5}\s*\n?\s*[1-5]\s*조\s*\d{6}", text))
    lotto_count = len(re.findall(r"로또6/45\s*\n?\s*\d{1,5}\s*\n?\s*\d{5}(?:\s+\d{5}){5}", text))
    return f"구매내역 목록 감지. 로또 {lotto_count}건, 연금복권 {pension_count}건."


def _log(verbose: bool, message: str) -> None:
    if verbose:
        print(f"[scrape-ledger] {message}", flush=True)


def _close_dialog(page) -> None:
    try:
        page.keyboard.press("Escape")
    except Exception:
        pass
    for selector in ("#btn-pop-close", ".btn-pop-close", "button[title='닫기']", "[aria-label='닫기']"):
        try:
            locator = page.locator(selector)
            for index in range(locator.count()):
                candidate = locator.nth(index)
                if candidate.is_visible(timeout=500):
                    candidate.click(timeout=500)
                    return
        except Exception:
            continue
    for label in ("닫기", "확인", "close", "Close", "X", "×"):
        try:
            locator = page.get_by_text(label, exact=True)
            if locator.count() > 0:
                locator.first.click(timeout=500)
                return
        except Exception:
            continue


def _looks_like_ticket_text(text: str) -> bool:
    normalized = _normalize_text(text)
    return bool(re.search(r"\d{1,5}\s*회", normalized)) and (
        "로또" in normalized
        or "Lotto" in normalized
        or "연금복권" in normalized
        or re.search(r"[1-5]\s*조", normalized) is not None
        or re.search(r"\b[A-E]\b", normalized) is not None
    )


def _parse_ticket_texts(texts: Iterable[str]) -> ImportedTickets:
    lotto = []
    pension = []
    errors = []
    for text in texts:
        try:
            imported = parse_ticket_text(text)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        lotto.extend(imported.lotto)
        pension.extend(imported.pension)
    if not lotto and not pension:
        detail = f" 마지막 오류. {errors[-1]}" if errors else ""
        raise ValueError(f"구매내역에서 로또 또는 연금복권 티켓 번호를 찾지 못했습니다.{detail}")
    return ImportedTickets(tuple(_renumber_lotto_slots(lotto)), tuple(_renumber_pension_slots(pension)))


def _renumber_lotto_slots(tickets: Iterable[ImportedLottoTicket]) -> list[ImportedLottoTicket]:
    counters: dict[int, int] = {}
    renumbered = []
    for ticket in tickets:
        index = counters.get(ticket.round, 0)
        slot = chr(ord("A") + index) if index < 26 else str(index + 1)
        counters[ticket.round] = index + 1
        renumbered.append(ImportedLottoTicket(ticket.round, slot, ticket.numbers))
    return renumbered


def _renumber_pension_slots(tickets: Iterable[ImportedPensionTicket]) -> list[ImportedPensionTicket]:
    counters: dict[int, int] = {}
    renumbered = []
    for ticket in tickets:
        index = counters.get(ticket.round, 0) + 1
        counters[ticket.round] = index
        renumbered.append(
            ImportedPensionTicket(
                round=ticket.round,
                slot=str(index),
                group=ticket.group,
                number=ticket.number,
            )
        )
    return renumbered


def _unique_texts(texts: Iterable[str]) -> list[str]:
    seen = set()
    unique = []
    for text in texts:
        key = _normalize_text(text)
        if key in seen:
            continue
        seen.add(key)
        unique.append(text)
    return unique


def _normalize_text(text: str) -> str:
    return re.sub(r"[ \t]+", " ", text.replace("\r\n", "\n").replace("\r", "\n")).strip()
