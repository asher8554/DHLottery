# 이미 알림을 보낸 구매번호를 중복 처리하지 않도록 기록하는 모듈
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import hmac
import json
from pathlib import Path
from typing import Any


@dataclass
class SentState:
    path: Path
    sent: dict[str, dict[str, Any]]

    @classmethod
    def load(cls, path: str | Path) -> "SentState":
        state_path = Path(path)
        if not state_path.exists():
            return cls(path=state_path, sent={})
        try:
            data = json.loads(state_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return cls(path=state_path, sent={})
        sent = data.get("sent", {}) if isinstance(data, dict) else {}
        if not isinstance(sent, dict):
            sent = {}
        return cls(path=state_path, sent=sent)

    def is_sent(self, fingerprint: str) -> bool:
        return fingerprint in self.sent

    def mark_sent(self, fingerprint: str, game: str, round_no: int) -> None:
        self.sent[fingerprint] = {
            "game": game,
            "round": round_no,
            "sent_at": datetime.now(timezone.utc).isoformat(),
        }

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = {"sent": self.sent}
        tmp_path = self.path.with_name(f"{self.path.name}.tmp")
        tmp_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        tmp_path.replace(self.path)


def fingerprint_ticket(payload: dict[str, Any], salt: str = "") -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if salt:
        return hmac.new(salt.encode("utf-8"), raw, hashlib.sha256).hexdigest()
    return hashlib.sha256(raw).hexdigest()
