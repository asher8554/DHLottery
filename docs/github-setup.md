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
$bytes = New-Object byte[] 32
$rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
$rng.GetBytes($bytes)
[Convert]::ToBase64String($bytes)
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
$bytes = New-Object byte[] 32
$rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
$rng.GetBytes($bytes)
[Convert]::ToBase64String($bytes)
```

## 구매번호 입력 요령

- 로또 번호는 숫자 6개를 1부터 45 사이로 입력합니다.
- 연금복권 번호는 `group`에 조를, `number`에 6자리 번호를 문자열로 입력합니다.
- 앞자리가 0일 수 있으므로 연금복권 `number`는 반드시 따옴표로 감쌉니다.
- 실제 구매 회차를 알고 있다면 `round`에는 `latest` 대신 회차 숫자를 입력합니다.
- 로컬 테스트용 `tickets.yml`이나 `data/tickets.yml`은 커밋하지 않습니다.

## 로컬 tickets.yml을 TICKETS_YAML로 올리기

GitHub Actions는 내 PC의 `data/tickets.yml`을 직접 읽을 수 없습니다.
파일을 저장소에 커밋하면 구매번호가 노출될 수 있으므로 권장하지 않습니다.
대신 로컬 `data/tickets.yml` 내용을 GitHub Secret `TICKETS_YAML`로 업로드하세요.

GitHub CLI 로그인이 되어 있지 않다면 먼저 로그인합니다.

```powershell
gh auth login
```

그 다음 저장소 루트에서 아래 스크립트를 실행합니다.

```powershell
Set-Location E:\Github\DHLottery
.\scripts\sync-tickets-secret.ps1
```

다른 파일을 올리고 싶다면 경로를 지정할 수 있습니다.

```powershell
.\scripts\sync-tickets-secret.ps1 -Path data\tickets.yml
```

실제 업로드 전 검증만 하려면 `-DryRun`을 붙입니다.

```powershell
.\scripts\sync-tickets-secret.ps1 -DryRun
```

이 스크립트는 파일 내용을 화면에 출력하지 않고 GitHub CLI를 통해 Secret으로 업로드합니다.
구매번호를 바꿀 때마다 이 스크립트를 다시 실행하면 `TICKETS_YAML` Secret이 갱신됩니다.

## 수동 실행

1. 저장소의 `Actions` 탭으로 이동합니다.
2. `Check lottery results` 워크플로를 선택합니다.
3. `Run workflow`를 누릅니다.

처음 설정한 뒤에는 수동 실행으로 카카오톡 알림이 정상 동작하는지 확인하세요.
검사가 확정한 회차 요약은 `data/result-history.yml`에 누적되고, GitHub Pages의 `지난 당첨결과 이력` 영역에서 볼 수 있습니다.
이 파일에는 구매번호 원문을 저장하지 않고 날짜, 게임, 회차, 미당첨 개수, 당첨 등수 개수만 저장합니다.

## Pages에서 사용할 GitHub token 권한

Pages 화면에서 `당첨 검사 실행`과 `알림 시간 저장`을 쓰려면 GitHub fine-grained personal access token이 필요합니다.
토큰은 저장소 `asher8554/DHLottery` 하나에만 접근하도록 만들고, 아래 권한만 부여하세요.

- `Actions`: Read and write.

알림 시간 저장은 `Update notification settings` 워크플로를 실행하고, 실제 파일 커밋은 GitHub Actions의 기본 토큰이 처리합니다.
토큰은 기본적으로 브라우저 요청에만 사용되며, `이 브라우저에 토큰 저장`을 체크한 경우에만 현재 브라우저의 localStorage에 저장됩니다.

## 스케줄 변경

기본적으로 `.github/workflows/check-results.yml`은 10분마다 실행됩니다.
다만 실제 당첨 검사와 카카오톡 발송은 `data/notification-settings.yml`의 시간 설정에 맞을 때만 진행됩니다.
GitHub Pages 화면의 `카카오톡 알림 시간`에서 요일, 시간, 확인 허용 시간을 바꾼 뒤 `알림 시간 저장`을 누르세요.
발표 전 또는 사이트 결과 미반영 상태도 카카오톡으로 받고 싶다면 `발표 전 대기 상태도 카카오톡 알림`을 체크한 뒤 저장합니다.
체크하지 않으면 결과가 아직 준비되지 않았을 때는 카카오톡을 보내지 않고, 다음 실행에서 다시 확인합니다.

설정 파일을 직접 수정하고 싶다면 아래 형식을 사용합니다.

```yaml
notification_schedule:
  timezone: Asia/Seoul
  window_minutes: 30
  notify_pending: false
  lotto:
    enabled: true
    day: saturday
    time: "21:45"
  pension:
    enabled: true
    day: thursday
    time: "20:10"
```

`window_minutes`는 예약 실행이 조금 늦거나 동행복권 결과 반영이 늦을 때를 감안한 허용 시간입니다.
예를 들어 `time`이 `"21:45"`이고 `window_minutes`가 `30`이면 한국시간 21시 45분부터 22시 15분 전까지 실행된 작업만 실제 검사를 진행합니다.
