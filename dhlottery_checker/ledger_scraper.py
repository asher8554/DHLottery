# 로그인된 로컬 브라우저에서 구매내역 티켓 텍스트를 수집하는 모듈
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Iterable

from .ticket_import import ImportedTickets, parse_ticket_text, write_imported_tickets


LEDGER_URL = "https://www.dhlottery.co.kr/mypage/mylotteryledger"
HOME_URL = "https://www.dhlottery.co.kr/"
TICKET_BUTTON_PATTERN = re.compile(r"(티켓\s*보기|티켓보기|복권\s*보기|상세\s*보기|상세보기)")


@dataclass(frozen=True)
class ScrapeLedgerResult:
    imported_tickets: ImportedTickets
    ticket_text_count: int


def scrape_ledger_to_file(
    *,
    ticket_path: str | Path = "data/tickets.yml",
    profile_dir: str | Path = ".browser/dhlottery",
    ledger_url: str = LEDGER_URL,
    max_tickets: int = 30,
    headless: bool = False,
    append: bool = False,
) -> ScrapeLedgerResult:
    ticket_texts = scrape_ledger_ticket_texts(
        profile_dir=profile_dir,
        ledger_url=ledger_url,
        max_tickets=max_tickets,
        headless=headless,
    )
    imported_tickets = _parse_ticket_texts(ticket_texts)
    write_imported_tickets(ticket_path, imported_tickets, replace_all=not append)
    return ScrapeLedgerResult(imported_tickets, len(ticket_texts))


def scrape_ledger_ticket_texts(
    *,
    profile_dir: str | Path = ".browser/dhlottery",
    ledger_url: str = LEDGER_URL,
    max_tickets: int = 30,
    headless: bool = False,
) -> list[str]:
    try:
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

    with sync_playwright() as playwright:
        context = playwright.chromium.launch_persistent_context(
            user_data_dir=str(profile_path),
            headless=headless,
            viewport={"width": 1280, "height": 900},
            locale="ko-KR",
        )
        try:
            page = context.pages[0] if context.pages else context.new_page()
            if not headless:
                page.goto(HOME_URL, wait_until="domcontentloaded")
                print("브라우저에서 동행복권에 로그인하고 구매/당첨내역 페이지가 보이면 Enter를 누르세요.")
                input()
            page.goto(ledger_url, wait_until="domcontentloaded")
            page.wait_for_load_state("networkidle", timeout=10000)
            return _collect_ticket_texts(context, page, max_tickets, PlaywrightTimeoutError)
        finally:
            context.close()


def _collect_ticket_texts(context, page, max_tickets: int, timeout_error_type: type[Exception]) -> list[str]:
    texts: list[str] = []
    buttons = _ticket_button_handles(page)
    for handle in buttons[:max_tickets]:
        text = _text_after_click(context, page, handle, timeout_error_type)
        normalized = _normalize_text(text)
        if normalized and _looks_like_ticket_text(normalized):
            texts.append(normalized)

    if not texts:
        body_text = _body_text(page)
        if _looks_like_ticket_text(body_text):
            texts.append(_normalize_text(body_text))
    return _unique_texts(texts)


def _ticket_button_handles(page) -> list[object]:
    handles = page.query_selector_all("a, button, input[type='button'], input[type='submit']")
    ticket_handles = []
    for handle in handles:
        try:
            label = handle.evaluate(
                """
                (el) => [
                  el.innerText,
                  el.value,
                  el.getAttribute('aria-label'),
                  el.getAttribute('title'),
                  el.getAttribute('onclick')
                ].filter(Boolean).join(' ')
                """
            )
        except Exception:
            continue
        if is_ticket_button_label(str(label)):
            ticket_handles.append(handle)
    return ticket_handles


def is_ticket_button_label(label: str) -> bool:
    return bool(TICKET_BUTTON_PATTERN.search(_normalize_text(label)))


def _text_after_click(context, page, handle, timeout_error_type: type[Exception]) -> str:
    popup = None
    try:
        with context.expect_page(timeout=1500) as popup_info:
            handle.click(timeout=5000)
        popup = popup_info.value
        popup.wait_for_load_state("domcontentloaded", timeout=5000)
        return _body_text(popup)
    except timeout_error_type:
        page.wait_for_timeout(700)
        text = _body_text(page)
        _close_dialog(page)
        return text
    finally:
        if popup is not None:
            popup.close()


def _body_text(page) -> str:
    try:
        return page.locator("body").inner_text(timeout=5000)
    except Exception:
        return ""


def _close_dialog(page) -> None:
    try:
        page.keyboard.press("Escape")
    except Exception:
        pass
    for label in ("닫기", "확인", "close", "Close", "X"):
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
    return ImportedTickets(tuple(lotto), tuple(pension))


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
