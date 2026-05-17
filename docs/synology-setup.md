# 시놀로지에서 주간 자동 실행하기

이 문서는 시놀로지 DSM에서 동행복권 구매내역 스크래퍼를 매주 실행하고, `data/tickets.yml`과 `data/account.yml`을 GitHub에 푸시해 Pages와 카카오 알림 흐름까지 이어지게 만드는 절차입니다.

기준 경로는 실제 설치한 위치인 `/volume1/docker/Github/DHLottery`입니다. 다른 경로에 설치했다면 명령의 경로만 바꾸면 됩니다.

자동 충전과 간편비밀번호 자동 입력은 하지 않습니다.

## 전체 흐름

1. DSM 작업 스케줄러가 매주 `scripts/synology-docker-run.sh`를 실행합니다.
2. Docker 컨테이너 안에서 `scripts/scrape-ledger-and-push.sh`가 실행됩니다.
3. Playwright headless Chromium이 동행복권에 로그인합니다.
4. 구매내역의 상세 팝업 텍스트와 메인 전체메뉴의 예치금을 읽습니다.
5. `data/tickets.yml`과 `data/account.yml`을 커밋하고 GitHub에 푸시합니다.
6. GitHub Pages가 새 파일을 읽고, GitHub Actions가 당첨 확인과 예치금 부족 알림을 처리합니다.

## 준비물

- DSM의 Container Manager 또는 Docker 패키지.
- SSH 접속 권한.
- GitHub에 push 가능한 Deploy key.
- 동행복권 아이디와 비밀번호를 저장할 로컬 `.env`.
- GitHub Actions에 이미 설정한 카카오 Secret.

## 저장소 받기

시놀로지 호스트에 `git`이 없을 수 있으므로 Docker로 clone하는 방식을 기본으로 씁니다.

```bash
mkdir -p /volume1/docker/Github
cd /volume1/docker/Github
rm -rf DHLottery
docker run --rm -v "$PWD:/work" -w /work debian:bookworm-slim sh -lc \
  "apt-get update && apt-get install -y --no-install-recommends git ca-certificates && git clone https://github.com/asher8554/DHLottery.git"
cd DHLottery
```

clone은 HTTPS로 받고, push는 아래에서 만들 SSH key로 처리합니다.

원격 주소를 SSH push용으로 바꿉니다.

```bash
docker run --rm -v "$PWD:/work" -w /work debian:bookworm-slim sh -lc \
  "apt-get update && apt-get install -y --no-install-recommends git ca-certificates openssh-client && git remote set-url origin git@github.com:asher8554/DHLottery.git"
```

커밋 작성자를 설정합니다.

```bash
docker run --rm -v "$PWD:/work" -w /work debian:bookworm-slim sh -lc \
  "apt-get update && apt-get install -y --no-install-recommends git ca-certificates && git config user.name 'synology-dhlottery' && git config user.email 'synology-dhlottery@example.local'"
```

## SSH key 설정

컨테이너가 GitHub에 push하려면 SSH key가 필요합니다. 저장소 안의 `.ssh` 폴더를 컨테이너에 마운트하는 방식으로 사용합니다.

```bash
cd /volume1/docker/Github/DHLottery
mkdir -p .ssh
ssh-keygen -t ed25519 -C "synology-dhlottery" -f .ssh/id_ed25519
chmod 700 .ssh
chmod 600 .ssh/id_ed25519
chmod 644 .ssh/id_ed25519.pub
```

passphrase를 묻는다면 그냥 Enter를 눌러 빈 값으로 둡니다. 주간 자동 실행이 멈추지 않게 하기 위해서입니다.

GitHub 저장소의 `Settings`에서 `Deploy keys`로 들어가 `.ssh/id_ed25519.pub` 내용을 추가합니다. `Allow write access`를 켜야 push가 됩니다.

GitHub host key를 저장합니다.

```bash
docker run --rm -v "$PWD/.ssh:/root/.ssh" debian:bookworm-slim sh -lc \
  "apt-get update && apt-get install -y --no-install-recommends openssh-client ca-certificates && ssh-keyscan github.com >> /root/.ssh/known_hosts && chmod 644 /root/.ssh/known_hosts"
```

연결을 확인합니다.

```bash
docker run --rm \
  -v "$PWD:/work" \
  -w /work \
  -v "$PWD/.ssh:/root/.ssh" \
  debian:bookworm-slim sh -lc \
  "apt-get update && apt-get install -y --no-install-recommends git openssh-client ca-certificates && GIT_SSH_COMMAND='ssh -i /root/.ssh/id_ed25519 -o IdentitiesOnly=yes' git ls-remote origin"
```

성공하면 `HEAD`와 `refs/heads/main`이 포함된 해시 목록이 출력됩니다.

## .env 만들기

저장소 루트에 `.env`를 만듭니다. 이 파일은 `.gitignore`에 포함되어 커밋되지 않습니다.

```bash
cd /volume1/docker/Github/DHLottery
vi .env
```

내용은 아래처럼 둡니다.

```env
DHLOTTERY_ID=동행복권아이디
DHLOTTERY_PASSWORD=동행복권비밀번호
```

간편비밀번호나 결제 비밀번호는 넣지 않습니다.

## Docker 이미지 만들기

처음 한 번만 이미지를 빌드합니다.

```bash
cd /volume1/docker/Github/DHLottery
docker build -f Dockerfile.synology -t dhlottery-synology:latest .
```

Playwright Chromium과 필요한 Linux 패키지를 이미지에 넣기 때문에 빌드 시간이 몇 분 걸릴 수 있습니다.

## 최신 코드 받기

이미 `dhlottery-synology:latest` 이미지를 빌드했다면 이 명령으로 최신 코드를 받습니다.

```bash
cd /volume1/docker/Github/DHLottery
docker run --rm \
  -v "$PWD:/app" \
  -w /app \
  -v "$PWD/.ssh:/root/.ssh" \
  dhlottery-synology:latest bash -lc \
  "git config --global --add safe.directory /app && GIT_SSH_COMMAND='ssh -i /root/.ssh/id_ed25519 -o IdentitiesOnly=yes' git pull --rebase"
```

`cannot pull with rebase: You have unstaged changes`가 나오면 로컬 변경이 pull을 막고 있는 상태입니다. 시놀로지에서 문서를 직접 고친 적이 없다면 변경을 임시 보관한 뒤 pull합니다.

```bash
cd /volume1/docker/Github/DHLottery
docker run --rm \
  -v "$PWD:/app" \
  -w /app \
  -v "$PWD/.ssh:/root/.ssh" \
  dhlottery-synology:latest bash -lc \
  "git config --global --add safe.directory /app && git stash push -m synology-before-pull README.md checklist.md context-notes.md plan.md docs/synology-setup.md || true && GIT_SSH_COMMAND='ssh -i /root/.ssh/id_ed25519 -o IdentitiesOnly=yes' git pull --rebase"
```

`.ssh/`는 SSH key 보관 폴더라 Git에 올리지 않습니다. 최신 코드에는 `.ssh/`가 `.gitignore`에 들어 있습니다.

## 첫 실행 테스트

일반 사용자 계정은 Docker socket 권한이 없을 수 있으므로 root shell에서 실행하는 방식이 가장 간단합니다.

```bash
sudo su
cd /volume1/docker/Github/DHLottery
NO_PUSH=1 bash scripts/synology-docker-run.sh
```

성공하면 터미널에 아래와 비슷한 로그가 나옵니다.

```text
[scrape-ledger] 로그인 페이지 이동. https://www.dhlottery.co.kr/login
[scrape-ledger] 예치금 감지. 40,000원.
[scrape-ledger] 상세 버튼 1에서 티켓 텍스트 감지.
```

`NO_PUSH=1`은 GitHub에 푸시하지 않고 동작만 확인하는 옵션입니다.

정상 확인 후 실제 push까지 실행합니다.

```bash
cd /volume1/docker/Github/DHLottery
bash scripts/synology-docker-run.sh
```

실행 후 Pages에서 새 구매번호와 예치금을 확인합니다.

<https://asher8554.github.io/DHLottery/ticket-entry.html>

## DSM 작업 스케줄러 등록

DSM에서 `제어판`으로 들어갑니다.

`작업 스케줄러`에서 `생성`, `예약된 작업`, `사용자 정의 스크립트`를 선택합니다.

일반 탭은 아래처럼 설정합니다.

- 작업 이름은 `DHLottery weekly scrape`로 둡니다.
- 사용자는 `root`로 둡니다.
- 활성화를 켭니다.

스케줄 탭에서 원하는 주간 실행 시간을 고릅니다. 예를 들어 매주 일요일 오전 9시에 실행하도록 둘 수 있습니다.

작업 설정 탭의 사용자 정의 스크립트에는 아래 내용을 넣습니다.

```bash
REPO=/volume1/docker/Github/DHLottery
cd "$REPO" || exit 1
mkdir -p logs
bash scripts/synology-docker-run.sh >> logs/scrape-ledger.log 2>&1
```

구매 후 바로 반영하고 싶다면 root shell에서 같은 명령을 수동 실행하면 됩니다.

## 카카오 알림 시간과 맞추기

시놀로지 작업과 카카오톡 결과 알림은 역할이 다릅니다.
시놀로지는 동행복권 구매내역을 읽어 `data/tickets.yml`을 GitHub에 올립니다.
GitHub Actions는 Pages에서 설정한 카카오톡 알림 시간에 `data/tickets.yml`과 당첨번호를 비교한 뒤 메시지를 보냅니다.

따라서 카카오톡 알림이 의미 있으려면 결과 알림 시간보다 먼저 시놀로지 작업이 한 번 성공해야 합니다.
권장 흐름은 아래와 같습니다.

1. 동행복권에서 직접 복권을 구매합니다.
2. 시놀로지 작업 스케줄러가 구매내역을 읽고 GitHub에 푸시합니다.
3. Pages 화면에서 최신 구매번호가 보이는지 확인합니다.
4. 결과 발표 후 Pages에서 설정한 시간에 GitHub Actions가 카카오톡 결과 알림을 보냅니다.

예시 스케줄입니다.

- 로또만 산다면 토요일 20시 30분쯤 시놀로지 스크래퍼를 한 번 실행하고, Pages의 로또 카카오 알림 시간은 토요일 21시 45분쯤으로 둡니다.
- 연금복권도 산다면 목요일 19시 30분쯤 시놀로지 스크래퍼를 한 번 실행하고, Pages의 연금복권 카카오 알림 시간은 목요일 20시 10분쯤으로 둡니다.
- 구매 시간이 일정하지 않다면 구매 직후 DSM 작업을 수동 실행하거나, 시놀로지 스크래퍼를 하루 1회 실행하도록 잡아도 됩니다.

Pages의 `카카오톡 알림 시간`은 시놀로지 실행 시간이 아니라 결과 확인 시간입니다.
시놀로지 실행 시간이 늦어져 결과 확인 시간 이후에 `data/tickets.yml`이 올라가면 그 회차 알림은 다음 수동 실행이나 다음 예약 실행 때까지 오지 않을 수 있습니다.

## 로그 확인

작업 로그는 저장소 안의 `logs/scrape-ledger.log`에 쌓입니다.

```bash
cd /volume1/docker/Github/DHLottery
tail -n 120 logs/scrape-ledger.log
```

디버그 파일은 기존과 같은 위치에 저장됩니다.

- `.browser/debug/ledger-body.txt`.
- `.browser/debug/ledger-candidates.txt`.
- `.browser/debug/ledger-page.png`.

## 카카오톡 알림이 오지 않을 때

시놀로지 작업 스케줄러와 카카오톡 알림은 같은 단계가 아닙니다.
시놀로지는 구매내역과 예치금을 읽어 `data/tickets.yml`, `data/account.yml`을 GitHub에 푸시합니다.
카카오톡 결과 알림은 추첨 결과 발표 후 GitHub Actions의 `Check lottery results` 워크플로가 보냅니다.

먼저 아래 순서로 확인합니다.

1. DSM 작업 스케줄러의 마지막 실행 시간이 갱신되었는지 확인합니다.
2. `logs/scrape-ledger.log` 마지막 120줄을 확인합니다.
3. GitHub 저장소의 `Actions` 탭에서 `Check lottery results` 최근 실행이 성공했는지 확인합니다.
4. 해당 실행 로그에 `새로 알릴 결과가 없습니다.`가 있는지 확인합니다.
5. 해당 실행의 `Print check status` 단계에서 아래 값을 확인합니다.

```json
{
  "resolved_count": 10,
  "unsent_resolved_count": 0,
  "pending_count": 0,
  "pending_not_ready_count": 0,
  "sent_resolved_count": 0,
  "sent_pending_count": 0,
  "clear_tickets": false
}
```

`resolved_count`가 0보다 큰데 `unsent_resolved_count`가 0이면 결과는 확인됐지만 이미 보낸 것으로 판단한 상태입니다.
이 경우 다시 받고 싶다면 GitHub Pages에서 `카카오톡 강제 재전송`을 체크하고 `당첨 검사 실행`을 누르거나, GitHub Actions에서 `Check lottery results`를 수동 실행할 때 `force_notify`를 켭니다.

`pending_not_ready_count`가 0보다 크면 동행복권 사이트에 결과가 아직 반영되지 않았거나 일시적으로 조회에 실패한 상태입니다.
다음 스케줄 실행을 기다리거나 수동으로 다시 실행합니다.

`No ticket file. Nothing to check.`가 나오면 원격 `data/tickets.yml`이 비어 있거나 아직 푸시되지 않은 상태입니다.
시놀로지 작업 로그에서 `git push`가 성공했는지 확인합니다.

예치금 부족 알림은 `Check balance` 워크플로가 담당합니다.
최근 `Check balance` 실행 로그에서 `현재 예치금 ... 기준 ... 이하입니다.`가 출력되고 워크플로가 성공했다면 카카오 API 호출 자체는 성공한 것입니다.
휴대폰에서 나와의 채팅방 알림이 꺼져 있거나 이미 읽은 메시지로 처리되었는지도 확인합니다.

## VS Code Remote-SSH가 연결되지 않을 때

VS Code에서 `ssh: connect to host ... port 22: Permission denied`가 나오면 저장소 코드 문제가 아니라 시놀로지 SSH 접속 자체가 막힌 상태입니다.
아래를 DSM에서 확인합니다.

- `제어판`, `터미널 및 SNMP`에서 SSH 서비스가 켜져 있는지 확인합니다.
- SSH 포트가 22가 맞는지 확인합니다. 포트를 바꿨다면 VS Code SSH 설정에도 같은 포트를 넣어야 합니다.
- `제어판`, `보안`, `방화벽`에서 현재 PC IP가 SSH 포트에 접근 가능한지 확인합니다.
- `제어판`, `보안`, `계정`, 자동 차단 또는 허용/차단 목록에 현재 PC IP가 차단되어 있지 않은지 확인합니다.
- SSH 접속에 쓰는 사용자가 DSM에서 비활성화되지 않았는지 확인합니다.

SSH가 막혀도 DSM의 `File Station`에서 `logs/scrape-ledger.log`를 내려받거나, 작업 스케줄러의 실행 결과 화면으로 기본 진단은 가능합니다.

## 자주 생기는 문제

`/volume1/docker/DHLottery`로 이동할 수 없다는 오류가 나오면 실제 경로가 `/volume1/docker/Github/DHLottery`인지 확인합니다.

`git: command not found`가 나오면 시놀로지 호스트에 Git이 없는 상태입니다. 이 문서의 Docker Git 명령을 사용하면 됩니다.

`unable to get random bytes for temporary file`가 나오면 `alpine/git` 이미지가 DS916 계열과 맞지 않는 상황입니다. 이 문서의 `debian:bookworm-slim` 명령을 사용하면 됩니다.

`ssh-keyscan: command not found`가 나오면 이 문서의 Docker `ssh-keyscan` 명령을 사용합니다.

`Permission denied (publickey)`가 나오면 GitHub Deploy key의 공개키 등록과 `Allow write access`를 확인합니다.

`permission denied while trying to connect to the Docker daemon socket`이 나오면 일반 사용자에게 Docker 권한이 없는 상태입니다. `sudo su`로 root shell에 들어가 실행하거나, DSM 작업 스케줄러의 실행 사용자를 `root`로 바꿉니다.

`cannot pull with rebase: You have unstaged changes`가 나오면 로컬 변경이 pull을 막고 있는 상태입니다. 위의 `git stash push ... && git pull --rebase` 명령으로 정리합니다.

`detected dubious ownership`가 나오면 컨테이너 안에서 안전 경로 설정이 필요할 수 있습니다. 현재 스크립트가 `/app` 경로를 자동으로 `safe.directory`에 추가합니다.

동행복권 로그인이 실패하면 `.env`의 `DHLOTTERY_ID`, `DHLOTTERY_PASSWORD`를 다시 확인합니다. 사이트 정책이나 보안 확인 때문에 자동 로그인이 막히면 시놀로지 headless 실행이 어려울 수 있습니다.

`구매내역에서 로또 또는 연금복권 티켓 번호를 찾지 못했습니다`가 나오면 `.browser/debug` 파일을 확인합니다. 구매내역 화면에 대상 티켓이 없거나 동행복권 화면 구조가 바뀐 경우일 수 있습니다.

Docker 이미지 빌드가 실패하면 DSM의 Container Manager 또는 Docker가 정상 설치되어 있는지 확인합니다.

## 네이티브 Python으로 실행하고 싶을 때

Docker 대신 시놀로지에 Python, Git, Playwright Chromium 의존성을 직접 설치했다면 아래 스크립트를 사용할 수 있습니다.

```bash
cd /volume1/docker/Github/DHLottery
python3 -m pip install -r requirements.txt
python3 -m playwright install chromium
bash scripts/scrape-ledger-and-push.sh
```

다만 DSM 네이티브 환경은 Chromium 의존성 설치가 막힐 수 있어 Docker 방식을 권장합니다.
