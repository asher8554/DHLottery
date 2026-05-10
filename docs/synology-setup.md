# 시놀로지에서 주간 자동 실행하기

이 문서는 시놀로지 DSM에서 동행복권 구매내역 스크래퍼를 매주 실행하고, `data/tickets.yml`과 `data/account.yml`을 GitHub에 푸시해 Pages와 카카오 알림 흐름까지 이어지게 만드는 절차입니다.

## 동작 구조

시놀로지에서는 아래 순서로 동작합니다.

1. DSM 작업 스케줄러가 매주 `scripts/synology-docker-run.sh`를 실행합니다.
2. Docker 컨테이너 안에서 `scripts/scrape-ledger-and-push.sh`가 실행됩니다.
3. Playwright headless Chromium이 동행복권에 로그인합니다.
4. 구매내역의 상세 팝업 텍스트와 메인 전체메뉴의 예치금을 읽습니다.
5. `data/tickets.yml`과 `data/account.yml`을 커밋하고 GitHub에 푸시합니다.
6. GitHub Pages가 새 파일을 읽고, GitHub Actions가 당첨 확인과 예치금 부족 알림을 처리합니다.

자동 충전과 간편비밀번호 자동 입력은 하지 않습니다.

## 준비물

- DSM의 Container Manager 또는 Docker 패키지.
- SSH 접속 권한.
- GitHub에 push 가능한 SSH key.
- 동행복권 아이디와 비밀번호를 저장할 로컬 `.env`.
- GitHub Actions에 이미 설정한 카카오 Secret.

아래 예시는 사용자가 실제로 받은 저장소 위치인 `/volume1/docker/Github/DHLottery`를 기준으로 합니다. 다른 위치를 쓴다면 명령의 경로만 바꾸면 됩니다.

## 저장소 받기

SSH로 시놀로지에 접속한 뒤 저장소를 받을 폴더를 만듭니다.

```bash
mkdir -p /volume1/docker
mkdir -p /volume1/docker/Github
cd /volume1/docker/Github
git clone git@github.com:asher8554/DHLottery.git
cd DHLottery
```

만약 `git: command not found`가 나오면 시놀로지 호스트에 Git이 없는 상태입니다. Docker는 있으므로 Git이 들어있는 임시 컨테이너로 clone하면 됩니다.
DS916처럼 오래된 커널 계열에서는 `alpine/git`이 `unable to get random bytes for temporary file` 오류를 낼 수 있으므로 Debian 기반 컨테이너를 사용합니다.

```bash
mkdir -p /volume1/docker/Github
cd /volume1/docker/Github
rm -rf DHLottery
docker run --rm -v "$PWD:/work" -w /work debian:bookworm-slim sh -lc \
  "apt-get update && apt-get install -y --no-install-recommends git ca-certificates && git clone https://github.com/asher8554/DHLottery.git"
cd DHLottery
```

이 방식은 HTTPS로 공개 저장소를 clone합니다. 나중에 push는 아래에서 만들 SSH key와 `dhlottery-synology` 컨테이너 안의 Git으로 처리합니다.

HTTPS로 이미 받은 저장소라면 push 자동화를 위해 SSH 원격으로 바꾸는 편이 편합니다.

```bash
git remote set-url origin git@github.com:asher8554/DHLottery.git
```

호스트에 Git이 없다면 위 명령도 Docker Git으로 실행합니다.

```bash
docker run --rm -v "$PWD:/work" -w /work debian:bookworm-slim sh -lc \
  "apt-get update && apt-get install -y --no-install-recommends git ca-certificates openssh-client && git remote set-url origin git@github.com:asher8554/DHLottery.git"
```

커밋 작성자도 한 번 설정합니다.

```bash
git config user.name "synology-dhlottery"
git config user.email "synology-dhlottery@example.local"
```

호스트에 Git이 없다면 커밋 작성자 설정도 Docker Git으로 실행합니다.

```bash
docker run --rm -v "$PWD:/work" -w /work debian:bookworm-slim sh -lc \
  "apt-get update && apt-get install -y --no-install-recommends git ca-certificates && git config user.name 'synology-dhlottery' && git config user.email 'synology-dhlottery@example.local'"
```

## SSH key 설정

컨테이너가 GitHub에 push하려면 SSH key가 필요합니다. 이 문서는 저장소 안의 `.ssh` 폴더를 컨테이너에 마운트하는 방식으로 설명합니다.

```bash
cd /volume1/docker/Github/DHLottery
mkdir -p .ssh
ssh-keygen -t ed25519 -C "synology-dhlottery" -f .ssh/id_ed25519
chmod 700 .ssh
chmod 600 .ssh/id_ed25519
chmod 644 .ssh/id_ed25519.pub
```

GitHub 저장소의 `Settings`에서 `Deploy keys`로 들어가 `.ssh/id_ed25519.pub` 내용을 추가합니다. `Allow write access`를 켜야 push가 됩니다.

처음 연결할 때 known hosts를 저장합니다.

```bash
ssh-keyscan github.com >> .ssh/known_hosts
chmod 644 .ssh/known_hosts
```

만약 `ssh-keyscan: command not found`가 나오면 Docker로 `ssh-keyscan`을 실행합니다.

```bash
mkdir -p .ssh
docker run --rm -v "$PWD/.ssh:/root/.ssh" debian:bookworm-slim sh -lc \
  "apt-get update && apt-get install -y --no-install-recommends openssh-client ca-certificates && ssh-keyscan github.com >> /root/.ssh/known_hosts && chmod 644 /root/.ssh/known_hosts"
```

연결 확인은 아래처럼 합니다.

```bash
GIT_SSH_COMMAND="ssh -i .ssh/id_ed25519 -o IdentitiesOnly=yes" git ls-remote origin
```

호스트에 Git이 없으면 연결 확인도 Docker로 실행합니다.

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

## 첫 실행 테스트

먼저 push 없이 동작만 확인하고 싶으면 아래처럼 실행합니다.

```bash
cd /volume1/docker/Github/DHLottery
NO_PUSH=1 bash scripts/synology-docker-run.sh
```

성공하면 터미널에 아래와 비슷한 로그가 나옵니다.

```text
[scrape-ledger] 로그인 페이지 이동. https://www.dhlottery.co.kr/login
[scrape-ledger] 예치금 감지. 40,000원.
[scrape-ledger] 상세 버튼 1에서 티켓 텍스트 감지.
```

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
- 사용자는 Docker 실행 권한이 있는 계정 또는 `root`로 둡니다.
- 활성화를 켭니다.

SSH에서 일반 사용자로 실행했을 때 `permission denied while trying to connect to the Docker daemon socket`이 나오면 Docker 권한이 없는 계정입니다. DSM 작업 스케줄러에서는 사용자를 `root`로 두는 것이 가장 간단합니다.

스케줄 탭에서 원하는 주간 실행 시간을 고릅니다. 예를 들어 매주 일요일 오전 9시에 실행하도록 둘 수 있습니다.

작업 설정 탭의 사용자 정의 스크립트에는 아래 내용을 넣습니다.

```bash
REPO=/volume1/docker/Github/DHLottery
cd "$REPO" || exit 1
mkdir -p logs
bash scripts/synology-docker-run.sh >> logs/scrape-ledger.log 2>&1
```

구매 후 바로 반영하고 싶다면 수동으로도 같은 명령을 실행하면 됩니다.

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

## 자주 생기는 문제

`Permission denied (publickey)`가 나오면 GitHub Deploy key의 공개키 등록과 `Allow write access`를 확인합니다.

`detected dubious ownership`가 나오면 컨테이너 안에서 안전 경로 설정이 필요할 수 있습니다. 현재 스크립트가 `/app` 경로를 자동으로 `safe.directory`에 추가합니다.

동행복권 로그인이 실패하면 `.env`의 `DHLOTTERY_ID`, `DHLOTTERY_PASSWORD`를 다시 확인합니다. 사이트 정책이나 보안 확인 때문에 자동 로그인이 막히면 시놀로지 headless 실행이 어려울 수 있습니다.

`구매내역에서 로또 또는 연금복권 티켓 번호를 찾지 못했습니다`가 나오면 `.browser/debug` 파일을 확인합니다. 구매내역 화면에 대상 티켓이 없거나 동행복권 화면 구조가 바뀐 경우일 수 있습니다.

Docker 이미지 빌드가 실패하면 DSM의 Container Manager 또는 Docker가 정상 설치되어 있는지 확인합니다.

Docker 실행에서 `permission denied while trying to connect to the Docker daemon socket`이 나오면 `sudo su`로 root shell에 들어가 실행하거나, DSM 작업 스케줄러의 실행 사용자를 `root`로 바꿉니다.

## 네이티브 Python으로 실행하고 싶을 때

Docker 대신 시놀로지에 Python, Git, Playwright Chromium 의존성을 직접 설치했다면 아래 스크립트를 사용할 수 있습니다.

```bash
cd /volume1/docker/Github/DHLottery
python3 -m pip install -r requirements.txt
python3 -m playwright install chromium
bash scripts/scrape-ledger-and-push.sh
```

다만 DSM 네이티브 환경은 Chromium 의존성 설치가 막힐 수 있어 Docker 방식을 권장합니다.
