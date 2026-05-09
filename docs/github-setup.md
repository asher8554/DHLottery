# GitHub 설정 가이드

## 저장소 private 전환

실제 구매번호와 알림 상태를 외부에 노출하지 않으려면 저장소를 private로 바꾸는 것을 권장합니다.

1. GitHub 저장소 `asher8554/DHLottery`에 접속합니다.
2. `Settings`로 이동합니다.
3. `General` 페이지의 `Danger Zone`에서 저장소 공개 범위를 private로 변경합니다.
4. 확인 문구를 입력하고 변경을 완료합니다.

## GitHub Actions Secrets

저장소의 `Settings`에서 `Secrets and variables`, `Actions`, `New repository secret` 순서로 이동해 아래 값을 추가합니다.

`TICKETS_YAML`

```yaml
lotto:
  tickets:
    - label: "이번 주 로또"
      round: 1223
      numbers: [1, 2, 3, 4, 5, 6]

pension:
  tickets:
    - label: "이번 주 연금복권"
      round: 315
      group: 1
      number: "123456"
```

`KAKAO_REST_API_KEY`

Kakao Developers 앱의 REST API 키입니다.

`KAKAO_REFRESH_TOKEN`

카카오 OAuth 토큰 발급 단계에서 받은 refresh token입니다.

`KAKAO_CLIENT_SECRET`

Kakao Developers 앱에서 REST API 키의 Client Secret이 `ON`인 경우에만 추가합니다.
Client Secret이 `OFF`라면 생략해도 됩니다.

`STATE_HASH_SALT`

중복 알림 방지 상태 파일에 구매번호 원문 대신 지문값을 저장하기 위한 임의 문자열입니다.
예를 들어 긴 랜덤 문장이나 비밀번호 생성기로 만든 값을 넣으면 됩니다.

## 구매번호 입력 요령

- 로또 번호는 숫자 6개를 1부터 45 사이로 입력합니다.
- 연금복권 번호는 `group`에 조를, `number`에 6자리 번호를 문자열로 입력합니다.
- 앞자리가 0일 수 있으므로 연금복권 `number`는 반드시 따옴표로 감쌉니다.
- 실제 구매 회차를 알고 있다면 `round`에는 `latest` 대신 회차 숫자를 입력합니다.

## 수동 실행

1. 저장소의 `Actions` 탭으로 이동합니다.
2. `Check lottery results` 워크플로를 선택합니다.
3. `Run workflow`를 누릅니다.

처음 설정한 뒤에는 수동 실행으로 카카오톡 알림이 정상 동작하는지 확인하세요.

## 스케줄 변경

`.github/workflows/check-results.yml`의 cron 값을 바꾸면 됩니다.
GitHub Actions cron은 UTC 기준입니다.

예를 들어 한국시간 토요일 21시 20분은 UTC 토요일 12시 20분입니다.

```yaml
- cron: "20 12 * * 6"
```
