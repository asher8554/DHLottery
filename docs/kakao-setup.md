# 카카오톡 알림 설정 가이드

카카오톡 나에게 보내기를 사용하려면 Kakao Developers 앱과 OAuth 토큰이 필요합니다.

## 앱 만들기

1. <https://developers.kakao.com/>에 접속합니다.
2. `내 애플리케이션`에서 새 앱을 만듭니다.
3. 앱의 `REST API 키`를 복사해 둡니다.
4. `제품 설정`의 `카카오 로그인`을 활성화합니다.
5. Redirect URI에 `http://localhost:8080/oauth`를 추가합니다.
6. 동의항목에서 카카오톡 메시지 전송 권한을 설정합니다.

## 인증 코드 받기

아래 주소에서 `REST_API_KEY`를 본인의 REST API 키로 바꾼 뒤 브라우저에서 엽니다.

```text
https://kauth.kakao.com/oauth/authorize?client_id=REST_API_KEY&redirect_uri=http://localhost:8080/oauth&response_type=code&scope=talk_message
```

로그인과 동의를 마치면 브라우저가 `http://localhost:8080/oauth?code=...` 형태의 주소로 이동합니다.
페이지가 열리지 않아도 괜찮습니다.
주소창의 `code` 값을 복사하면 됩니다.

## 토큰 받기

PowerShell에서 아래 명령을 실행합니다.
`REST_API_KEY`와 `PASTE_CODE_HERE`를 본인의 값으로 바꿔야 합니다.

```powershell
$body = @{
  grant_type = "authorization_code"
  client_id = "REST_API_KEY"
  redirect_uri = "http://localhost:8080/oauth"
  code = "PASTE_CODE_HERE"
}

Invoke-RestMethod -Uri "https://kauth.kakao.com/oauth/token" -Method Post -Body $body
```

응답에서 `refresh_token`을 복사합니다.
GitHub Secret에는 `access_token`보다 `refresh_token`을 넣는 편이 낫습니다.

## GitHub Secret에 넣을 값

- `KAKAO_REST_API_KEY`에는 REST API 키를 넣습니다.
- `KAKAO_REFRESH_TOKEN`에는 위 단계에서 받은 refresh token을 넣습니다.

## 토큰이 만료된 경우

카카오 정책에 따라 refresh token도 만료될 수 있습니다.
알림이 실패하면 이 문서의 인증 코드 받기와 토큰 받기 단계를 다시 진행한 뒤 `KAKAO_REFRESH_TOKEN` Secret을 새 값으로 교체하세요.

