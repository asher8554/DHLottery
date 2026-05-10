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

## 티켓 보기 붙여넣기 입력

동행복권에서 직접 구매한 뒤 `티켓 보기` 화면의 텍스트를 복사하면 로또 선택번호를 자동으로 `data/tickets.yml`에 반영할 수 있습니다.
아이디, 비밀번호, 예치금 정보는 저장하거나 자동 입력하지 않습니다.
아래처럼 회차와 숫자 6개만 복사해도 됩니다.

```text
1224
9
12
13
33
35
43
```

티켓 보기 화면 전체를 복사한 경우에도 `A`, `B`, `C`, `D`, `E` 게임 줄을 찾아 여러 게임을 한 번에 입력할 수 있습니다.

1. 동행복권에서 로그인하고 구매내역 또는 티켓 보기 화면을 엽니다.
2. `A 자동 9 12 13 33 35 43`처럼 실제 선택번호가 보이는 부분까지 복사합니다.
3. 저장소 루트에서 아래 명령을 실행합니다.

```powershell
.\scripts\import-ticket.ps1 -ReplaceAll
```

처음 실제 티켓으로 바꾸거나 로또만 관리한다면 `-ReplaceAll`을 쓰면 됩니다.
연금복권 항목은 유지하고 로또 항목만 교체하려면 `-ReplaceLotto`를 씁니다.
기존 `data/tickets.yml`에 로또 항목을 누적하고 싶다면 두 옵션을 모두 빼고 실행합니다.
GitHub Secret까지 바로 갱신하려면 아래처럼 실행합니다.

```powershell
.\scripts\import-ticket.ps1 -ReplaceAll -SyncSecret
```

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
.\scripts\scrape-ledger.ps1
```

스크립트는 먼저 `https://www.dhlottery.co.kr/login`으로 이동해 로그인 폼을 확인한 뒤, 자동 로그인 후 `https://www.dhlottery.co.kr/mypage/mylotteryledger`로 이동합니다.

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
.\scripts\scrape-ledger.ps1 -Append
```

로그인 세션을 지우고 싶으면 `.browser` 폴더를 삭제하면 됩니다.
티켓 번호를 찾지 못하면 현재 화면 텍스트가 `.browser/debug/ledger-body.txt`에 저장됩니다.
화면에 티켓이 보이는데도 실패하면 이 파일에서 `티켓보기`, `복권번호보기`, `A 자동` 같은 문구가 있는지 확인하면 다음 수정 지점을 바로 잡을 수 있습니다.

## 웹 입력 화면 예시

GitHub Pages에 올릴 수 있는 정적 입력 화면 예시는 [docs/ticket-entry.html](docs/ticket-entry.html)에 있습니다.
로또 6/45와 연금복권720+ 입력 탭을 구분해 `tickets.yml` 내용을 생성하고, GitHub Actions를 실행해 공개 `data/tickets.yml`에 커밋할 수 있습니다.
배포 후 주소는 <https://asher8554.github.io/DHLottery/> 입니다.
입력 화면은 다크모드 토글을 제공하고, 선택한 화면 모드는 같은 브라우저에 저장됩니다.

웹에서 GitHub에 저장하려면 GitHub fine-grained token을 입력합니다.
토큰은 기본적으로 요청에만 사용하고, `이 브라우저에 토큰 저장`을 체크하면 현재 브라우저에 저장합니다.
토큰 권한은 저장소 `asher8554/DHLottery`에 대해 `Actions: Read and write`면 됩니다.
저장이 끝나면 `Update ticket and check results` 워크플로가 `data/tickets.yml`을 커밋하고 당첨 확인을 실행합니다.
이미 보낸 결과를 카카오톡으로 다시 받고 싶으면 웹 입력 화면에서 `강제 재전송`을 체크합니다.
카카오 알림은 전체 결과를 빠르게 보는 요약 메시지와 맞은 번호를 확인하는 상세 메시지로 나뉘어 발송됩니다.
요약 메시지는 당첨 항목이 있을 때 로또 A-E 슬롯이나 연금복권 번호와 등수를 함께 보여줍니다.
요약 메시지에는 동행복권 결과 페이지 링크도 함께 포함됩니다.

## GitHub Actions 실행

워크플로는 `.github/workflows/check-results.yml`에 있습니다.
기본 스케줄은 한국시간 기준 연금복권 목요일 19시 15분, 로또 토요일 21시 10분입니다.
GitHub cron은 UTC 기준이라 파일에는 각각 `15 10 * * 4`, `10 12 * * 6`으로 적혀 있습니다.

발표 반영이 늦어지는 날을 고려해 즉시 확인하지 않도록 잡았습니다.
동행복권 조회가 일시적으로 시간 초과되면 몇 번 재시도하고, 끝까지 실패하면 다음 실행에서 다시 확인하도록 실패 결과를 상태에 저장하지 않습니다.
원하면 워크플로 파일의 cron만 바꾸면 됩니다.

## 설정 문서

- GitHub 저장소와 Secret 설정은 [docs/github-setup.md](docs/github-setup.md)를 보세요.
- 카카오톡 나에게 보내기 설정은 [docs/kakao-setup.md](docs/kakao-setup.md)를 보세요.
- 로컬 `data/tickets.yml`을 GitHub Secret으로 올릴 때는 `scripts/sync-tickets-secret.ps1`을 사용할 수 있습니다.
- 다음 작업을 이어갈 때는 [handoff.md](handoff.md)를 먼저 보세요.

## 테스트

```powershell
python -m unittest discover -s tests
```
