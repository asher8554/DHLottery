# GitHub 설정 가이드

## 저장소 private 전환

실제 구매번호와 알림 상태를 외부에 노출하지 않으려면 저장소를 private로 바꾸는 것을 권장합니다.

1. GitHub 저장소 `asher8554/DHLottery`에 접속합니다.
2. `Settings`로 이동합니다.
3. `General` 페이지의 `Danger Zone`에서 저장소 공개 범위를 private로 변경합니다.
4. 확인 문구를 입력하고 변경을 완료합니다.

## GitHub Actions Secrets

저장소의 `Settings`에서 `Secrets and variables`, `Actions`, `New repository secret` 순서로 이동해 아래 값을 추가합니다.
Secret 이름은 대소문자를 포함해 아래와 정확히 같아야 합니다.

필수 Secret입니다.

- `TICKETS_YAML`
- `KAKAO_REST_API_KEY`
- `KAKAO_REFRESH_TOKEN`
- `STATE_HASH_SALT`

조건부 Secret입니다.

- `KAKAO_CLIENT_SECRET`: Kakao Developers 앱에서 Client Secret이 `ON`인 경우에만 추가합니다.

`TICKETS_YAML`

실제 구매번호 전체를 YAML 형식으로 넣습니다.
GitHub 화면에서는 여러 줄 Secret을 그대로 붙여넣을 수 있습니다.

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
PowerShell에서는 아래 명령으로 만들 수 있습니다.

```powershell
[Convert]::ToBase64String([System.Security.Cryptography.RandomNumberGenerator]::GetBytes(32))
```

출력된 문자열 전체를 `STATE_HASH_SALT` Secret 값에 넣습니다.
이 값은 다시 볼 필요가 없고, 채팅이나 파일에 붙여넣지 않는 편이 좋습니다.

## TICKETS_YAML 오류가 나는 경우

Actions에서 아래 오류가 나면 `TICKETS_YAML` Secret이 없거나 이름이 틀린 것입니다.

```text
GitHub Actions에서 구매번호를 찾지 못했습니다. Repository secret에 TICKETS_YAML을 추가했는지 확인하세요.
```

확인할 항목입니다.

- 저장소 `Settings`, `Secrets and variables`, `Actions`에 들어갔는지 확인합니다.
- `Repository secrets`에 `TICKETS_YAML`이 있는지 확인합니다.
- `Environment secrets`가 아니라 `Repository secrets`에 넣었는지 확인합니다.
- Secret 이름이 `TICKET_YAML`, `TICKETS`, `tickets_yaml`처럼 다르게 들어가지 않았는지 확인합니다.
- `TICKETS_YAML` 값이 비어 있지 않은지 확인합니다.

## STATE_HASH_SALT 오류가 나는 경우

Actions에서 아래 오류가 나면 `STATE_HASH_SALT` Secret이 없거나 이름이 틀린 것입니다.

```text
STATE_HASH_SALT is required.
```

`STATE_HASH_SALT`는 구매번호를 중복 알림 방지 상태 파일에 그대로 남기지 않기 위한 임의 문자열입니다.
GitHub 저장소의 `Settings`, `Secrets and variables`, `Actions`, `New repository secret`에서 아래 이름으로 추가하세요.

```text
STATE_HASH_SALT
```

값은 아래 PowerShell 명령으로 만든 문자열을 넣으면 됩니다.

```powershell
[Convert]::ToBase64String([System.Security.Cryptography.RandomNumberGenerator]::GetBytes(32))
```

## 구매번호 입력 요령

- 로또 번호는 숫자 6개를 1부터 45 사이로 입력합니다.
- 연금복권 번호는 `group`에 조를, `number`에 6자리 번호를 문자열로 입력합니다.
- 앞자리가 0일 수 있으므로 연금복권 `number`는 반드시 따옴표로 감쌉니다.
- 실제 구매 회차를 알고 있다면 `round`에는 `latest` 대신 회차 숫자를 입력합니다.
- 로컬 테스트용 `tickets.yml`이나 `data/tickets.yml`은 커밋하지 않습니다.

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
