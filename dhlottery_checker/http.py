# 동행복권과 카카오 HTTP 호출을 처리하는 모듈
from __future__ import annotations

import json
import time
from typing import Any
from urllib import error, parse, request


USER_AGENT = "DHLotteryChecker/0.1 (+https://github.com/asher8554/DHLottery)"


class HttpError(RuntimeError):
    pass


def get_json(url: str, params: dict[str, Any] | None = None, timeout: int = 20) -> dict[str, Any]:
    text = get_text(url, params=params, timeout=timeout, accept="application/json")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise HttpError(_html_error_message(text, url)) from exc
    if not isinstance(data, dict):
        raise HttpError(f"JSON 응답이 객체가 아닙니다. {url}")
    return data


def get_text(
    url: str,
    params: dict[str, Any] | None = None,
    timeout: int = 20,
    accept: str = "text/html,application/json",
    retries: int = 2,
    retry_delay: float = 1.5,
) -> str:
    target = _with_params(url, params)
    req = request.Request(
        target,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": accept,
        },
        method="GET",
    )
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            with request.urlopen(req, timeout=timeout) as response:
                charset = response.headers.get_content_charset() or "utf-8"
                return response.read().decode(charset, errors="replace")
        except error.HTTPError as exc:
            last_error = exc
            if not _should_retry_http_error(exc) or attempt >= retries:
                detail = _http_error_detail(exc)
                raise HttpError(f"HTTP 요청에 실패했습니다. {target}. {detail}") from exc
        except OSError as exc:
            last_error = exc
            if attempt >= retries:
                raise HttpError(f"HTTP 요청에 실패했습니다. {target}") from exc
        time.sleep(retry_delay * (attempt + 1))
    raise HttpError(f"HTTP 요청에 실패했습니다. {target}") from last_error


def post_form(url: str, data: dict[str, Any], headers: dict[str, str] | None = None, timeout: int = 20) -> dict[str, Any]:
    encoded = parse.urlencode(data).encode("utf-8")
    req_headers = {
        "User-Agent": USER_AGENT,
        "Content-Type": "application/x-www-form-urlencoded;charset=utf-8",
        "Accept": "application/json",
    }
    if headers:
        req_headers.update(headers)
    req = request.Request(url, data=encoded, headers=req_headers, method="POST")
    try:
        with request.urlopen(req, timeout=timeout) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            text = response.read().decode(charset, errors="replace")
    except error.HTTPError as exc:
        detail = _http_error_detail(exc)
        raise HttpError(f"HTTP POST 요청에 실패했습니다. {url}. {detail}") from exc
    except OSError as exc:
        raise HttpError(f"HTTP POST 요청에 실패했습니다. {url}") from exc
    try:
        result = json.loads(text)
    except json.JSONDecodeError as exc:
        raise HttpError(f"JSON 응답을 해석하지 못했습니다. {url}") from exc
    if not isinstance(result, dict):
        raise HttpError(f"JSON 응답이 객체가 아닙니다. {url}")
    return result


def _with_params(url: str, params: dict[str, Any] | None) -> str:
    if not params:
        return url
    query = parse.urlencode({key: value for key, value in params.items() if value is not None})
    separator = "&" if "?" in url else "?"
    return f"{url}{separator}{query}"


def _html_error_message(text: str, url: str) -> str:
    if "간소화 페이지" in text:
        return f"동행복권 간소화 페이지가 반환되었습니다. 잠시 후 다시 시도하세요. {url}"
    if "서비스 접근 대기" in text or "접속이 불가능" in text:
        return f"동행복권 접속 대기 또는 차단 페이지가 반환되었습니다. 잠시 후 다시 시도하세요. {url}"
    return f"JSON 대신 HTML 또는 알 수 없는 응답을 받았습니다. {url}"


def _http_error_detail(exc: error.HTTPError) -> str:
    charset = exc.headers.get_content_charset() if exc.headers else None
    raw = exc.read().decode(charset or "utf-8", errors="replace")
    if not raw:
        return f"상태 코드 {exc.code}"
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return f"상태 코드 {exc.code}, 응답 {raw[:300]}"
    if not isinstance(data, dict):
        return f"상태 코드 {exc.code}, 응답 {raw[:300]}"

    error_code = data.get("error_code")
    error_name = data.get("error")
    description = data.get("error_description") or data.get("msg") or data.get("message")
    parts = [f"상태 코드 {exc.code}"]
    if error_name:
        parts.append(f"error={error_name}")
    if error_code:
        parts.append(f"error_code={error_code}")
    if description:
        parts.append(f"description={description}")
    return ", ".join(parts)


def _should_retry_http_error(exc: error.HTTPError) -> bool:
    return exc.code == 429 or exc.code >= 500
