# 카카오톡 알림 설정 가이드

이 프로젝트는 카카오톡 채널, 푸시 알림, 친구에게 보내기를 쓰지 않습니다.
필요한 기능은 `카카오톡 메시지`의 `나에게 보내기`입니다.
공식 문서 기준으로는 `talk_message` 동의항목이 있는 액세스 토큰이 필요합니다.

## 준비물

- 본인 카카오 계정.
- Kakao Developers 앱.
- 앱의 REST API 키.
- 카카오 로그인으로 발급받은 refresh token.
- Client Secret이 켜져 있다면 Client Secret 값.

## 1. 앱 만들기

1. <https://developers.kakao.com/>에 접속합니다.
2. 카카오 계정으로 로그인합니다.
3. 상단의 `내 애플리케이션`으로 이동합니다.
4. `애플리케이션 추가하기` 또는 `앱 추가`를 누릅니다.
5. 앱 이름은 예를 들어 `DHLottery 알림`으로 입력합니다.
6. 사업자명 또는 회사명은 개인 용도라면 본인 이름이나 식별 가능한 이름으로 입력합니다.
7. 저장합니다.

## 2. REST API 키 확인

1. 방금 만든 앱을 엽니다.
2. `앱 설정` 또는 `요약 정보` 화면으로 이동합니다.
3. `앱 키` 영역에서 `REST API 키`를 복사합니다.
4. 이 값은 나중에 GitHub Secret의 `KAKAO_REST_API_KEY`에 넣습니다.

## 3. 제품 링크 관리 설정

카카오톡 메시지의 기본 템플릿은 링크 정보를 포함합니다.
공식 문서의 사전 설정에도 `제품 링크 관리`가 포함되어 있습니다.

1. 앱 화면에서 `제품 설정` 또는 `앱 설정`을 찾습니다.
2. `제품 링크 관리` 메뉴로 이동합니다.
3. `웹 도메인`에 아래 값을 추가합니다.

```text
https://www.dhlottery.co.kr
```

메뉴가 보이지 않으면 카카오 화면의 검색이나 왼쪽 메뉴에서 `제품 링크 관리` 또는 `웹 도메인`을 찾아보세요.

## 4. 카카오 로그인 활성화

1. 앱 화면에서 `제품 설정`으로 이동합니다.
2. `카카오 로그인`을 엽니다.
3. `활성화 설정`을 `ON`으로 바꿉니다.
4. 저장 버튼이 있으면 저장합니다.

## 5. Redirect URI 등록

1. `제품 설정`의 `카카오 로그인` 화면에서 `Redirect URI` 또는 `리다이렉트 URI` 항목을 찾습니다.
2. `Redirect URI 등록` 또는 `수정`을 누릅니다.
3. 아래 주소를 정확히 추가합니다.

```text
http://localhost:8080/oauth
```

주의할 점이 있습니다.
`https`가 아니라 `http`입니다.
끝에 `/oauth`가 있어야 합니다.
뒤에 `/`를 하나 더 붙이지 않습니다.

## 6. 동의항목에서 talk_message 설정

1. `제품 설정`의 `카카오 로그인`으로 이동합니다.
2. `동의항목` 메뉴를 엽니다.
3. `카카오톡 메시지 전송` 항목을 찾습니다.
4. 항목 ID 또는 scope가 `talk_message`인지 확인합니다.
5. 설정 버튼이 있다면 사용하도록 설정합니다.

화면에 `필수 동의`, `선택 동의`, `이용 중 동의` 같은 선택지가 있을 수 있습니다.
개인용 나에게 보내기에서는 `talk_message` 권한을 사용자가 동의할 수 있으면 됩니다.
이 문서의 인증 URL에 `scope=talk_message`를 넣기 때문에, 카카오가 필요한 동의 화면을 띄웁니다.

`카카오톡 메시지 전송` 항목이 아예 보이지 않으면 아래를 확인하세요.

- 앱의 카카오 로그인이 활성화되어 있는지 확인합니다.
- `동의항목` 화면에서 검색어로 `메시지`, `카카오톡`, `talk_message`를 찾아봅니다.
- 메뉴명이 `카카오 로그인 > 동의항목`인지, `제품 설정 > 카카오 로그인 > 동의항목`인지 확인합니다.

## 7. Client Secret 확인

카카오 공식 문서에는 REST API 키의 Client Secret이 기본 활성화될 수 있다고 안내되어 있습니다.
Client Secret이 `ON`이면 토큰 발급과 갱신 요청에 `client_secret`을 함께 보내야 합니다.

1. 앱 화면에서 `앱 설정`으로 이동합니다.
2. `플랫폼 키` 또는 `앱 키` 메뉴를 엽니다.
3. `REST API 키` 근처의 `Client Secret` 또는 `클라이언트 시크릿`을 찾습니다.
4. 상태가 `ON`이면 값을 복사합니다.
5. 이 값은 GitHub Secret의 `KAKAO_CLIENT_SECRET`에 넣습니다.

Client Secret이 `OFF`라면 `KAKAO_CLIENT_SECRET`은 만들지 않아도 됩니다.
다만 화면에서 값이 보이고 `ON`이라면 넣는 쪽으로 진행하세요.

## 8. 인증 코드 받기

아래 주소에서 `REST_API_KEY`를 본인의 REST API 키로 바꿉니다.
바꾼 주소를 브라우저 주소창에 붙여넣고 엽니다.

```text
https://kauth.kakao.com/oauth/authorize?client_id=REST_API_KEY&redirect_uri=http://localhost:8080/oauth&response_type=code&scope=talk_message
```

카카오 로그인과 동의를 마치면 브라우저가 아래와 비슷한 주소로 이동합니다.

```text
http://localhost:8080/oauth?code=긴_문자열
```

로컬 서버를 켜지 않았기 때문에 페이지가 열리지 않거나 오류 화면이 나와도 괜찮습니다.
주소창에 있는 `code=` 뒤의 긴 문자열만 복사하면 됩니다.
이 인증 코드는 한 번만 사용할 수 있고 오래 유지되지 않으므로 바로 다음 단계를 진행하세요.

## 9. 토큰 받기

PowerShell에서 아래 명령을 실행합니다.
세 값은 본인의 값으로 바꿔야 합니다.
Client Secret이 `OFF`라면 `$clientSecret`은 빈 문자열로 두면 됩니다.

```powershell
$restApiKey = "REST_API_KEY"
$authCode = "PASTE_CODE_HERE"
$clientSecret = ""

# Client Secret이 ON이면 위 줄 대신 아래 줄을 사용하세요.
# $clientSecret = "CLIENT_SECRET"

$body = @{
  grant_type = "authorization_code"
  client_id = $restApiKey
  redirect_uri = "http://localhost:8080/oauth"
  code = $authCode
}

if ($clientSecret -ne "" -and $clientSecret -ne "CLIENT_SECRET_IF_ON") {
  $body.client_secret = $clientSecret
}

Invoke-RestMethod `
  -Uri "https://kauth.kakao.com/oauth/token" `
  -Method Post `
  -ContentType "application/x-www-form-urlencoded;charset=utf-8" `
  -Body $body
```

성공하면 응답에 `access_token`, `refresh_token`, `expires_in` 같은 값이 나옵니다.
GitHub에는 `refresh_token`을 저장합니다.
`access_token`은 짧게 만료되므로 저장하지 않아도 됩니다.

## 10. GitHub Secrets에 넣기

GitHub 저장소에서 `Settings`, `Secrets and variables`, `Actions`, `New repository secret` 순서로 이동합니다.
아래 값을 추가합니다.

- `KAKAO_REST_API_KEY`에 REST API 키를 넣습니다.
- `KAKAO_REFRESH_TOKEN`에 토큰 응답의 `refresh_token`을 넣습니다.
- `KAKAO_CLIENT_SECRET`에 Client Secret 값을 넣습니다. Client Secret이 `OFF`라면 생략합니다.

## 11. 로컬에서 먼저 테스트하기

GitHub에 넣기 전에 로컬 PowerShell에서 한 번 보내볼 수 있습니다.
아래 값은 본인의 값으로 바꿉니다.

```powershell
$env:KAKAO_REST_API_KEY = "REST_API_KEY"
$env:KAKAO_REFRESH_TOKEN = "REFRESH_TOKEN"

# Client Secret이 ON인 경우에만 다음 줄을 실행하세요.
# $env:KAKAO_CLIENT_SECRET = "CLIENT_SECRET"

python -m dhlottery_checker check --tickets data\tickets.example.yml --notify --no-state
```

Client Secret이 `OFF`라면 아래처럼 비워도 됩니다.

```powershell
Remove-Item Env:\KAKAO_CLIENT_SECRET -ErrorAction SilentlyContinue
```

테스트가 성공하면 본인 카카오톡의 나와의 채팅방에 메시지가 옵니다.
예시 파일은 일부러 당첨 예시 번호를 담고 있으므로 실제 사용 전에는 GitHub Secret의 `TICKETS_YAML`을 본인 번호로 바꿔야 합니다.

## 자주 나는 오류

`KOE006` 또는 redirect URI 오류가 나옵니다.
등록한 Redirect URI와 인증 URL의 `redirect_uri`가 한 글자도 다르면 발생합니다.
둘 다 `http://localhost:8080/oauth`인지 확인하세요.

`KOE010`, `client_secret`, `invalid_client` 관련 오류가 나옵니다.
Client Secret이 `ON`인데 토큰 요청에 빠졌거나 값이 틀렸을 가능성이 큽니다.
`KAKAO_CLIENT_SECRET` 값을 다시 확인하세요.

`talk_message` 동의 또는 권한 관련 오류가 나옵니다.
동의항목에서 `카카오톡 메시지 전송(talk_message)`이 사용 가능하게 되어 있는지 확인하고, 인증 코드 받기 주소에 `scope=talk_message`가 들어 있는지 확인하세요.

`refresh_token`이 없거나 알림이 계속 실패합니다.
인증 코드는 한 번만 사용할 수 있습니다.
인증 코드 받기 단계부터 다시 진행해 새 토큰을 발급받으세요.

## 공식 문서

- 카카오톡 메시지 REST API 문서. <https://developers.kakao.com/docs/latest/ko/kakaotalk-message/rest-api>
- 카카오 로그인 REST API 문서. <https://developers.kakao.com/docs/latest/ko/kakaologin/rest-api>
- 카카오 로그인 설정 문서. <https://developers.kakao.com/docs/latest/ko/kakaologin/prerequisite>
