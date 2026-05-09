# 동행복권과 카카오 HTTP 호출을 처리하는 모듈
from __future__ import annotations

import json
from typing import Any
from urllib import parse, request


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
    try:
        with request.urlopen(req, timeout=timeout) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            return response.read().decode(charset, errors="replace")
    except OSError as exc:
        raise HttpError(f"HTTP 요청에 실패했습니다. {target}") from exc


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

