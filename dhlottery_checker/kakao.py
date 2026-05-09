# 카카오톡 나에게 보내기 메시지를 발송하는 모듈
from __future__ import annotations

import json
import os
from typing import Iterable

from .http import HttpError, post_form


KAKAO_TOKEN_URL = "https://kauth.kakao.com/oauth/token"
KAKAO_MEMO_URL = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
DEFAULT_LINK = "https://www.dhlottery.co.kr/"


class KakaoConfigError(RuntimeError):
    pass


def send_kakao_text(text: str) -> None:
    access_token = _access_token()
    for chunk in _split_message(text):
        template_object = {
            "object_type": "text",
            "text": chunk,
            "link": {
                "web_url": DEFAULT_LINK,
                "mobile_web_url": DEFAULT_LINK,
            },
        }
        response = post_form(
            KAKAO_MEMO_URL,
            {"template_object": json.dumps(template_object, ensure_ascii=False)},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if response.get("result_code") != 0:
            raise HttpError("카카오톡 메시지 발송에 실패했습니다.")


def _access_token() -> str:
    direct_token = os.environ.get("KAKAO_ACCESS_TOKEN", "").strip()
    if direct_token:
        return direct_token

    rest_api_key = os.environ.get("KAKAO_REST_API_KEY", "").strip()
    refresh_token = os.environ.get("KAKAO_REFRESH_TOKEN", "").strip()
    client_secret = os.environ.get("KAKAO_CLIENT_SECRET", "").strip()
    if not rest_api_key or not refresh_token:
        raise KakaoConfigError("KAKAO_REST_API_KEY와 KAKAO_REFRESH_TOKEN이 필요합니다.")

    data = {
        "grant_type": "refresh_token",
        "client_id": rest_api_key,
        "refresh_token": refresh_token,
    }
    if client_secret:
        data["client_secret"] = client_secret

    response = post_form(
        KAKAO_TOKEN_URL,
        data,
    )
    access_token = str(response.get("access_token", "")).strip()
    if not access_token:
        raise KakaoConfigError("카카오 액세스 토큰을 갱신하지 못했습니다.")
    return access_token


def _split_message(text: str, limit: int = 180) -> Iterable[str]:
    lines = text.splitlines() or [text]
    chunk = ""
    for line in lines:
        candidate = line if not chunk else f"{chunk}\n{line}"
        if len(candidate) <= limit:
            chunk = candidate
            continue
        if chunk:
            yield chunk
        while len(line) > limit:
            yield line[:limit]
            line = line[limit:]
        chunk = line
    if chunk:
        yield chunk
