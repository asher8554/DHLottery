# HTTP 재시도 처리를 검증하는 테스트
from __future__ import annotations

import socket
import unittest
from unittest.mock import MagicMock, patch

from dhlottery_checker.http import get_text


class HttpTest(unittest.TestCase):
    def test_get_text_retries_timeout(self):
        response = MagicMock()
        response.__enter__.return_value.headers.get_content_charset.return_value = "utf-8"
        response.__enter__.return_value.read.return_value = b"ok"

        with patch("dhlottery_checker.http.request.urlopen", side_effect=[socket.timeout("timed out"), response]):
            with patch("dhlottery_checker.http.time.sleep") as sleep:
                result = get_text("https://example.com", retries=1, retry_delay=0)

        self.assertEqual(result, "ok")
        sleep.assert_called_once()


if __name__ == "__main__":
    unittest.main()
