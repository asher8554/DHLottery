# DHLottery

동행복권에서 직접 구매한 로또 6/45와 연금복권720+ 번호를 당첨번호와 비교하고, 결과를 카카오톡 나에게 보내기로 알리는 도구입니다.

## 중요한 제한

이 저장소는 복권 자동 구매, 예치금 충전, 은행이체를 구현하지 않습니다.
공식 구매 API가 확인되지 않았고, 계정 및 금융정보 자동화는 보안과 약관 리스크가 큽니다.
구매내역 가져오기는 로컬 브라우저에서 사용자가 직접 로그인한 세션의 티켓 보기 텍스트만 읽습니다.

## 보안 원칙

- 실제 구매번호는 `tickets.yml` 또는 GitHub Actions Secret `TICKETS_YAML`에만 둡니다.
- `tickets.yml`은 `.gitignore`에 포함되어 커밋되지 않습니다.
- 카카오 토큰은 GitHub Actions Secrets에만 저장합니다.
- 카카오 Client Secret이 켜져 있다면 `KAKAO_CLIENT_SECRET`도 Secret에 저장합니다.
- 저장소는 private로 운영하는 것을 전제로 합니다.
- 동행복권 로그인 세션은 로컬 `.browser/` 폴더에만 보관되며 `.gitignore`로 커밋되지 않습니다.

## 로컬 실행

아래 명령으로 로컬에서 예시 파일을 확인할 수 있습니다.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item data\tickets.example.yml tickets.yml
python -m dhlottery_checker check --tickets tickets.yml --dry-run --no-state
```

`tickets.yml`에는 실제 구매 회차와 번호를 입력합니다.
회차를 정확히 알고 있다면 `round`에 숫자를 넣는 것이 가장 안전합니다.
`latest`도 지원하지만 발표 직후에는 최신 회차 반영이 늦을 수 있으므로 일반 사용에는 숫자 회차를 권장합니다.

## 로컬 구매내역 자동 가져오기

붙여넣기 대신 로컬 브라우저에서 동행복권 구매/당첨내역을 열고 티켓 보기 내용을 자동으로 가져올 수 있습니다.
비밀번호를 `.env`에 넣어 두면 열린 브라우저의 로그인 폼에 자동 입력하고, 값이 없으면 열린 브라우저에서 직접 로그인합니다.
로그인 세션은 저장소 안의 `.browser/dhlottery` 폴더에만 남습니다.

처음 한 번은 Playwright 브라우저를 설치합니다.

```powershell
python -m pip install -r requirements.txt
python -m playwright install chromium
```

이후 아래 명령을 실행합니다.

```powershell
.\scripts\scrape-ledger-and-push.ps1 -ShowProgress
```

스크립트는 먼저 `https://www.dhlottery.co.kr/login`으로 이동해 로그인 폼을 확인한 뒤, 자동 로그인 후 `https://www.dhlottery.co.kr/mypage/mylotteryledger`로 이동합니다.
초록 돋보기 상세 팝업을 열어 구매번호를 읽고 `data/tickets.yml`을 갱신한 다음 커밋과 푸시까지 진행합니다.
푸시가 끝나면 Pages 화면의 생성 결과가 원격 `data/tickets.yml` 내용으로 표시됩니다.

비밀번호를 매번 입력하지 않으려면 로컬 `.env`에 아래 값을 넣습니다.
`.env`는 `.gitignore`에 포함되어 커밋되지 않습니다.

```env
DHLOTTERY_PASSWORD=내비밀번호
```

아이디가 자동으로 채워지지 않는 환경이면 아이디도 함께 넣을 수 있습니다.

```env
DHLOTTERY_ID=내아이디
DHLOTTERY_PASSWORD=내비밀번호
```

브라우저가 열리면 `.env` 값으로 로그인 폼을 자동 제출합니다.
자동 로그인이 실패하거나 비밀번호가 없으면 직접 로그인하고 구매/당첨내역 화면이 보이는 상태에서 터미널로 돌아와 Enter를 누릅니다.
기본 동작은 가져온 구매번호로 `data/tickets.yml`을 교체합니다.
기존 항목에 누적하려면 `-Append`를 붙입니다.

```powershell
.\scripts\scrape-ledger-and-push.ps1 -Append -ShowProgress
```

로컬 파일 생성만 확인하고 원격 푸시는 미루려면 `-NoPush`를 붙입니다.

```powershell
.\scripts\scrape-ledger-and-push.ps1 -ShowProgress -NoPush
```

로그인 세션을 지우고 싶으면 `.browser` 폴더를 삭제하면 됩니다.
티켓 번호를 찾지 못하면 현재 화면 텍스트가 `.browser/debug/ledger-body.txt`에 저장됩니다.
상세 버튼 후보 정보는 `.browser/debug/ledger-candidates.txt`에 저장됩니다.
화면에 티켓이 보이는데도 실패하면 이 파일에서 `티켓보기`, `복권번호보기`, `A 자동` 같은 문구가 있는지 확인하면 다음 수정 지점을 바로 잡을 수 있습니다.

## Pages 생성 결과 확인

Pages 화면은 [docs/ticket-entry.html](docs/ticket-entry.html)에 있습니다.
배포 후 주소는 <https://asher8554.github.io/DHLottery/> 입니다.
직접 입력 화면이 아니라 GitHub에 저장된 `data/tickets.yml`을 읽어 생성 결과와 구매번호 요약을 표시합니다.
스크래퍼 푸시 후 화면에서 `새로고침`을 누르면 최신 구매번호를 다시 불러옵니다.
당첨 검사가 완료된 회차는 `data/result-history.yml`에 번호 없이 요약 이력으로 저장되고, Pages의 `지난 당첨결과 이력` 영역에서 확인할 수 있습니다.
다크모드 토글을 제공하고, 선택한 화면 모드는 같은 브라우저에 저장됩니다.

웹에서 당첨 검사를 바로 실행하려면 GitHub fine-grained token을 입력합니다.
토큰은 기본적으로 요청에만 사용하고, `이 브라우저에 토큰 저장`을 체크하면 현재 브라우저에 저장합니다.
토큰 권한은 저장소 `asher8554/DHLottery`에 대해 `Actions: Read and write`가 필요합니다.
`당첨 검사 실행` 버튼은 `Check lottery results` 워크플로를 실행합니다.
이미 보낸 결과를 카카오톡으로 다시 받고 싶으면 `카카오톡 강제 재전송`을 체크합니다.
`카카오톡 알림 시간`에서 로또와 연금복권의 요일, 시간, 확인 허용 시간을 바꾼 뒤 `알림 시간 저장`을 누르면 설정 갱신 워크플로가 실행되고 `data/notification-settings.yml`이 갱신됩니다.
발표 전 또는 동행복권 사이트 결과 미반영 상태도 카카오톡으로 받고 싶을 때만 `발표 전 대기 상태도 카카오톡 알림`을 체크합니다.
기본값은 꺼짐이라 결과가 아직 나오지 않았을 때는 카카오톡을 보내지 않습니다.
카카오 알림은 전체 결과를 빠르게 보는 요약 메시지와 맞은 번호를 확인하는 상세 메시지로 나뉘어 발송됩니다.
요약 메시지는 당첨 항목이 있을 때 로또 A-E 슬롯이나 연금복권 번호와 등수를 함께 보여줍니다.
요약 메시지에는 동행복권 결과 페이지 링크도 함께 포함됩니다.

## GitHub Actions 실행

워크플로는 `.github/workflows/check-results.yml`에 있습니다.
GitHub Actions cron은 10분마다 실행되지만, 실제 당첨 검사와 카카오톡 발송은 `data/notification-settings.yml`에 저장된 시간 안에서만 진행됩니다.
기본 설정은 사이트 결과 반영 지연을 고려해 한국시간 기준 연금복권 목요일 20시 10분, 로또 토요일 21시 45분입니다.
Pages 화면에서 시간을 바꾸면 별도 코드 수정 없이 다음 예약 실행부터 반영됩니다.

동행복권 사이트 결과 반영이 발표 후 최대 1시간 정도 늦어질 수 있어 발표 직후가 아니라 약 1시간 뒤에 확인하도록 잡았습니다.
동행복권 조회가 일시적으로 시간 초과되면 몇 번 재시도하고, 끝까지 실패하면 다음 실행에서 다시 확인하도록 실패 결과를 상태에 저장하지 않습니다.
`확인 허용 시간(분)`은 GitHub Actions 실행 지연과 동행복권 반영 지연을 흡수하는 범위입니다.
예를 들어 로또 시간이 21시 45분이고 확인 허용 시간이 30분이면 21시 45분부터 22시 15분 전까지 실행된 예약 작업만 실제 검사를 진행합니다.

## 설정 문서

- GitHub 저장소와 Secret 설정은 [docs/github-setup.md](docs/github-setup.md)를 보세요.
- 카카오톡 나에게 보내기 설정은 [docs/kakao-setup.md](docs/kakao-setup.md)를 보세요.
- 시놀로지에서 매주 자동 실행하려면 [docs/synology-setup.md](docs/synology-setup.md)를 보세요.
- 로컬 `data/tickets.yml`을 GitHub Secret으로 올릴 때는 `scripts/sync-tickets-secret.ps1`을 사용할 수 있습니다.
- 다음 작업을 이어갈 때는 [handoff.md](handoff.md)를 먼저 보세요.

## 테스트

```powershell
python -m unittest discover -s tests
```
