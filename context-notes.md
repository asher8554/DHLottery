# 컨텍스트 노트

## 2026-05-09

- 사용자는 만 19세 이상이며 본인 명의 계정 사용을 확인했다.
- 구매 자동화와 은행이체 자동화는 구현하지 않기로 했다.
- 이유는 공식 구매 API가 확인되지 않았고, 로그인 자동화와 금융거래 자동화는 보안 및 약관 리스크가 크기 때문이다.
- 구현 범위는 구매번호 기록, 당첨 확인, 카카오톡 알림, 구매 리마인더로 제한한다.
- 저장소는 비공개로 운영하는 전제를 둔다.
- 실제 구매번호는 외부에 노출되지 않아야 하므로 예시 파일만 커밋하고 실제 설정 파일은 `.gitignore`에 포함한다.
- 발표 직후 오판을 피하기 위해 실행 시간은 설정으로 쉽게 바꿀 수 있게 한다.
- 실제 구매번호는 로컬 `tickets.yml` 또는 GitHub Actions Secret `TICKETS_YAML`에서 읽는다.
- 중복 알림을 줄이기 위해 구매번호 자체가 아니라 지문값만 상태 파일에 저장한다.
- 로또 결과는 동행복권의 `/lt645/selectPstLt645InfoNew.do` 조회 결과를 사용한다.
- 연금복권 결과는 동행복권의 `/pt720/selectPstPt720WnList.do` 조회 결과를 사용한다.
- GitHub Actions 기본 실행 시간은 한국시간 연금복권 목요일 19시 15분, 로또 토요일 21시 10분으로 설정했다.
- GitHub Actions cron은 UTC 기준이므로 문서에 한국시간 변환 예시를 적었다.
- 카카오 설정은 사용자가 직접 Kakao Developers에서 앱과 토큰을 만든 뒤 Secret에 저장하는 방식으로 안내한다.
- 단위 테스트 9개가 통과했다.
- 예시 구매번호 파일로 실제 동행복권 조회를 실행했고 로또와 연금복권 결과 메시지가 생성되는 것을 확인했다.
- 첫 구현 커밋을 생성했다.

## 2026-05-09 카카오 설정 가이드 보강

- 사용자가 Kakao Developers 화면과 문서 내용이 달라 진행이 어렵다고 피드백했다.
- 공식 카카오 문서를 다시 확인했다.
- 나에게 보내기 API는 `https://kapi.kakao.com/v2/api/talk/memo/default/send`를 사용하며 액세스 토큰과 `talk_message` 동의가 필요하다.
- 공식 카카오 로그인 문서에는 REST API 키의 Client Secret이 기본 활성화될 수 있고, 활성화 상태라면 토큰 발급과 갱신 요청에 `client_secret`을 포함해야 한다고 안내되어 있다.
- 프로그램도 `KAKAO_CLIENT_SECRET` 환경변수를 선택적으로 읽어 토큰 갱신 요청에 포함하도록 변경했다.
- 카카오 설정 문서는 앱 생성, REST API 키, 제품 링크 관리, 카카오 로그인, Redirect URI, 동의항목, Client Secret, 토큰 발급, GitHub Secret, 로컬 테스트 순서로 다시 작성했다.
- 단위 테스트 9개와 예시 구매번호 dry-run을 다시 실행해 통과를 확인했다.
- 카카오 알림 설정 가이드 보강 커밋을 생성했다.

## 2026-05-09 카카오 401 오류 안내 보강

- 사용자가 인가 코드로 토큰을 받는 단계에서 PowerShell `Invoke-RestMethod` 401 오류를 받았다.
- PowerShell은 기본 오류 출력에서 카카오의 JSON 에러 본문을 숨길 수 있으므로 try/catch로 응답 본문을 읽는 절차를 문서에 추가했다.
- 토큰 요청 401의 흔한 원인으로 빈 변수, 이미 사용한 인증 코드, 다른 앱의 REST API 키, Redirect URI 불일치, Client Secret 설정 불일치를 정리했다.
- 카카오 401 오류 안내 보강 커밋을 생성할 예정이다.

## 2026-05-09 로컬 실행 위치 안내 보강

- 사용자가 `C:\Users\asher`에서 `python -m dhlottery_checker ...`를 실행해 `No module named dhlottery_checker` 오류를 받았다.
- 원인은 현재 작업 위치가 저장소 루트가 아니라 Python이 로컬 패키지를 찾지 못한 것이다.
- 카카오 설정 문서의 로컬 테스트 절차에 `Set-Location E:\Github\DHLottery` 단계를 추가했다.
- 로컬 실행 위치 안내 보강 커밋을 생성할 예정이다.

## 2026-05-09 카카오 HTTP 오류 출력 개선

- 사용자가 저장소 루트에서 로컬 알림 테스트를 실행했고 당첨번호 조회와 결과 생성은 성공했다.
- 카카오 알림 전송 전 `refresh_token`으로 access token을 갱신하는 단계에서 `https://kauth.kakao.com/oauth/token` 401 오류가 발생했다.
- 기존 HTTP 래퍼가 `urllib.error.HTTPError`의 응답 본문을 버려 카카오의 실제 오류 코드가 보이지 않았다.
- HTTP 오류 본문이 JSON이면 `error`, `error_code`, `error_description`을 프로그램 오류 메시지에 포함하도록 수정했다.
- 이전에 토큰 원문이 채팅에 노출된 적이 있으므로 새 refresh token 발급과 환경변수 재설정을 문서화했다.
- 단위 테스트 9개와 예시 구매번호 dry-run을 다시 실행해 통과를 확인했다.
- 카카오 HTTP 오류 출력 개선 커밋을 생성할 예정이다.

## 2026-05-09 GitHub Actions TICKETS_YAML 안내 보강

- 사용자가 GitHub Actions 수동 실행에서 `구매번호 설정 파일이 없습니다. tickets.yml` 오류를 받았다.
- 원인은 GitHub Actions에 로컬 `tickets.yml`이 없고 `TICKETS_YAML` Secret도 없거나 비어 있어 설정을 읽지 못한 것이다.
- GitHub Actions 환경에서는 `TICKETS_YAML` Secret 누락을 직접 안내하는 오류를 내도록 수정했다.
- GitHub 설정 문서에 필수 Secret 목록과 `TICKETS_YAML` 확인 절차를 추가했다.
- GitHub Actions 워크플로에도 필수 Secret 사전 확인 단계를 추가해 Python 실행 전 `TICKETS_YAML`, `KAKAO_REST_API_KEY`, `KAKAO_REFRESH_TOKEN`, `STATE_HASH_SALT` 누락을 표시하도록 했다.
- 단위 테스트 9개와 예시 구매번호 dry-run을 다시 실행해 통과를 확인했다.
- GitHub Actions TICKETS_YAML 안내 보강 커밋을 생성할 예정이다.

## 2026-05-09 STATE_HASH_SALT 안내 보강

- 사용자가 GitHub Actions에서 `Missing repository secret STATE_HASH_SALT is required.` 오류를 확인했다.
- 원인은 필수 Secret 중 `STATE_HASH_SALT`가 아직 등록되지 않은 것이다.
- `STATE_HASH_SALT`는 중복 알림 방지 상태 파일에 구매번호 원문 대신 지문값을 저장할 때 쓰는 임의 문자열이다.
- GitHub 설정 문서에 PowerShell 랜덤 문자열 생성 명령과 Secret 추가 절차를 추가했다.
- 로컬 실제 구매번호 파일 보호를 더 명확히 하기 위해 `.gitignore`에 `data/tickets.yml`과 `data/tickets.*.local.yml`을 추가했다.
- STATE_HASH_SALT 안내 보강 커밋을 생성할 예정이다.

## 2026-05-09 STATE_HASH_SALT PowerShell 호환성 보강

- 사용자의 PowerShell 환경에서 `[System.Security.Cryptography.RandomNumberGenerator]::GetBytes(32)` 정적 메서드가 없어 명령이 실패했다.
- 구버전 .NET/Windows PowerShell과 호환되도록 `RandomNumberGenerator.Create()` 인스턴스를 만든 뒤 byte 배열을 채우는 명령으로 문서를 수정했다.
- 새 PowerShell 난수 생성 명령이 로컬 환경에서 동작하는 것을 확인했다.
- STATE_HASH_SALT PowerShell 호환성 보강 커밋을 생성할 예정이다.

## 2026-05-09 tickets.yml Secret 동기화 보강

- 사용자가 `TICKETS_YAML`을 `tickets.yml`에서 자동으로 불러오고 싶다고 요청했다.
- GitHub Actions가 내 PC의 무시된 `data/tickets.yml`을 직접 읽을 수는 없고, 파일을 커밋하는 방식은 구매번호 노출 위험이 있다.
- 안전한 방향으로 로컬 `data/tickets.yml` 내용을 GitHub Secret `TICKETS_YAML`로 업로드하는 PowerShell 스크립트를 추가했다.
- GitHub CLI는 Secret 값을 로컬에서 암호화해 GitHub로 전송하므로 수동 복사보다 실수 가능성이 낮다.
- `scripts/sync-tickets-secret.ps1 -DryRun`과 단위 테스트 9개를 실행해 통과를 확인했다.
- tickets.yml Secret 동기화 보강 커밋을 생성할 예정이다.

## 2026-05-09 다음 작업 인수인계

- 사용자는 아직 실제 복권 구매를 해보지 않아 어떤 번호 입력 인터페이스가 편할지 감이 없다고 했다.
- 오늘은 여기까지만 코딩하고, 다음에 이어서 시작하기 좋은 md 파일 정리를 요청했다.
- `handoff.md`를 추가해 현재 상태, 운영 루틴, 필요한 Secret, 핵심 파일, 검증 명령, 다음 후보 작업, 하지 않기로 한 범위를 정리했다.
- 다음 작업 인수인계 커밋을 생성할 예정이다.

## 2026-05-10 티켓 붙여넣기 입력 도구

- 사용자가 실제 동행복권 로또6/45 티켓 보기 화면을 공유했다.
- 화면에서 `64315 53510 57779 62575 50796 26908`은 티켓 식별번호이고, 실제 선택번호는 `A 자동 9 12 13 33 35 43` 줄이다.
- 사용자는 구매/당첨내역 페이지를 자동 조회하려면 아이디와 비밀번호를 `.env`에 넣는 방식을 제안했다.
- 동행복권 계정과 예치금이 연결된 로그인 자동화는 이 프로젝트의 제외 범위이므로 구현하지 않는다.
- 대안으로 사용자가 로그인된 브라우저에서 티켓 보기나 구매내역의 텍스트를 복사하고, 로컬 명령이 그 텍스트에서 실제 선택번호만 추출해 `data/tickets.yml`을 갱신하는 방식으로 진행한다.
- `dhlottery_checker/ticket_import.py`를 추가해 로또6/45 티켓 보기 텍스트에서 회차와 `A`부터 `E`까지의 실제 게임 줄을 파싱하도록 했다.
- 기존 예시 티켓이 같이 확인되는 일을 막기 위해 첫 실제 가져오기용 `--replace-all`과 `-ReplaceAll` 옵션을 추가했다.
- PowerShell 파이프가 한글을 깨뜨릴 수 있어 `scripts/import-ticket.ps1`은 클립보드 텍스트를 임시 UTF-8 파일에 저장한 뒤 Python CLI에 넘긴다.
- `python -m unittest discover -s tests` 결과 13개 테스트가 통과했다.
- 임시 티켓 텍스트를 `import-ticket`으로 가져온 뒤 `check --dry-run --no-state`를 실행했고, 1224회 결과 대기 메시지까지 확인했다.

## 2026-05-10 간단 번호 입력 형식

- 사용자가 티켓 화면에서 번호만 복사하면 `1224회` 다음에 `9`, `12`, `13`, `33`, `35`, `43`이 줄바꿈된 형태가 될 것 같다고 했다.
- 같은 `import-ticket` 명령에서 티켓 전체 텍스트와 간단 번호 형식을 모두 처리하도록 확장한다.
- 간단 형식은 회차와 1부터 45 사이의 중복 없는 숫자 6개만 허용한다.
- 날짜나 티켓 식별번호처럼 45보다 큰 숫자가 섞이면 간단 형식으로 저장하지 않는다.
- `1224회`와 숫자 6개만 있는 텍스트를 `import-ticket`으로 가져온 뒤 `check --dry-run --no-state`를 실행했고, 1224회 결과 대기 메시지를 확인했다.
- `python -m unittest discover -s tests` 결과 14개 테스트가 통과했다.

## 2026-05-10 GitHub Pages 입력 화면 예시

- 사용자가 GitHub Pages에 입력 화면을 만들고, 회차와 번호 6개를 입력하면 파일 파싱을 쉽게 하는 방향을 제안했다.
- GitHub Pages는 정적 호스팅이므로 별도 인증 토큰 없이 저장소 파일이나 GitHub Actions Secret을 직접 수정할 수 없다.
- 안전한 예시 범위는 브라우저 안에서 `tickets.yml` 내용을 생성하고, 사용자가 복사하거나 다운로드한 뒤 기존 동기화 스크립트를 실행하는 것이다.
- 입력 화면은 로그인 정보, 토큰, 예치금 정보를 받지 않는다.
- `docs/ticket-entry.html`은 외부 라이브러리 없이 동작하는 정적 HTML로 만들었다.
- 화면은 회차와 번호 6개 직접 입력, 간단 붙여넣기 적용, YAML 복사, `tickets.yml` 내려받기를 제공한다.
- HTML 정적 검증으로 핵심 입력 요소와 `buildYaml`, `applyQuickText`, 다운로드 설정이 있는지 확인했다.
- `python -m unittest discover -s tests` 결과 14개 테스트가 통과했다.

## 2026-05-10 회차 숫자 붙여넣기 지원

- 사용자가 `1224` 다음 줄부터 번호 6개가 오는 형식으로 붙여넣기를 원한다고 했다.
- CLI 파서와 웹 입력 화면 모두 `1224회`뿐 아니라 첫 줄 `1224`를 회차로 인식하도록 수정한다.
- 간단 형식은 여전히 회차 1개와 1부터 45 사이 중복 없는 번호 6개만 허용한다.
- PowerShell `Set-Content -Encoding UTF8`이 만든 BOM이 첫 줄 숫자 앞에 붙어도 회차를 인식하도록 입력 줄 정규화에서 BOM을 제거한다.
- `python -m unittest discover -s tests` 결과 16개 테스트가 통과했다.
- `1224` 첫 줄 형식으로 임시 파일을 가져온 뒤 `check --dry-run --no-state`를 실행했고, 1224회 결과 대기 메시지를 확인했다.
- HTML 정적 검증으로 빠른 붙여넣기 기본값과 첫 줄 회차 처리 코드가 있는지 확인했다.

## 2026-05-10 GitHub Pages 배포 구성

- 사용자가 GitHub Pages로 UI를 확인할 수 있게 하고, 입력 후 GitHub 내 `ticket.yml`에 적용해 검사되도록 구성해 달라고 요청했다.
- `gh repo view asher8554/DHLottery --json visibility`로 확인한 결과 원격 저장소는 public이다.
- public 저장소에 실제 `data/tickets.yml`을 커밋하면 구매번호가 공개되므로 자동 커밋 방식은 구현하지 않는다.
- 우선 `docs/`를 GitHub Pages로 배포하는 Actions 워크플로를 추가한다.
- Pages 예상 주소는 `https://asher8554.github.io/DHLottery/`이다.
- `docs/index.html`은 Pages 루트 접근 시 `ticket-entry.html`로 이동한다.
- 워크플로 YAML 로딩 검증, Pages 정적 검증, 단위 테스트 16개를 실행해 통과를 확인했다.
- `gh api --method POST repos/asher8554/DHLottery/pages -f build_type=workflow`로 Pages를 GitHub Actions 배포 방식으로 활성화했다.
- `gh workflow run pages.yml --repo asher8554/DHLottery --ref main`으로 재배포했고 성공했다.
- `https://asher8554.github.io/DHLottery/`와 `/ticket-entry.html` 모두 HTTP 200 응답을 확인했다.

## 2026-05-10 공개 티켓 파일 갱신 자동화

- 사용자가 실제 로또 번호가 public 저장소에 공개되어도 상관없다고 명시했다.
- 따라서 `data/tickets.yml`을 더 이상 `.gitignore`로 숨기지 않고 공개 커밋 대상으로 전환한다.
- `update-ticket.yml` 워크플로는 Pages에서 받은 YAML을 `data/tickets.yml`에 쓰고 검증한 뒤 커밋한다.
- 같은 워크플로에서 선택적으로 당첨 확인과 카카오 알림까지 실행한다.
- 기존 `check-results.yml`은 더 이상 `TICKETS_YAML` Secret을 읽지 않고 공개 `data/tickets.yml`을 사용한다.
- Pages UI는 GitHub token을 브라우저 저장소에 저장하지 않고 workflow_dispatch 요청의 Authorization 헤더에만 사용한다.
- 웹에서 저장하려면 token에 `Actions: Read and write` 권한이 필요하다.
- `python -m unittest discover -s tests` 결과 16개 테스트가 통과했다.
- 워크플로 YAML 3개와 Pages HTML 정적 검증을 통과했다.
- 공개 `data/tickets.yml`로 `check --dry-run --no-state`를 실행했고 1224회 결과 대기 메시지를 확인했다.
- `dfeb6b3` 커밋을 원격에 푸시한 뒤 Pages 배포가 성공했다.
- `update-ticket.yml`을 `notify=false`로 실제 실행했고, 티켓 파일 검증과 커밋 단계가 성공했다.
- 같은 티켓 내용이라 원격 실행 로그에서 `No ticket changes to commit.`을 확인했다.
- 배포된 `ticket-entry.html`에서 `GitHub에 저장하고 검사` 버튼이 포함된 HTTP 200 응답을 확인했다.

## 2026-05-10 티켓 전체 붙여넣기 지원

- 사용자가 티켓 보기 전체 텍스트를 빠른 붙여넣기에 넣고 자동 파싱되기를 원했다.
- 예시 텍스트에는 회차, 발행일, 추첨일, 지급기한, 티켓 식별번호 6개, A-E 게임 블록이 포함되어 있다.
- 티켓 식별번호는 45보다 큰 숫자이므로 선택번호로 쓰지 않고, A-E 블록 아래의 1부터 45 사이 숫자만 선택번호로 읽는다.
- 파이썬 파서와 Pages 파서를 같은 규칙으로 맞춰 A-E 여러 게임을 모두 YAML로 생성한다.
- `python -m unittest discover -s tests` 결과 17개 테스트가 통과했다.
- 사용자가 준 전체 티켓 텍스트로 임시 YAML을 생성했고 A-E 5게임이 모두 결과 대기 메시지로 확인됐다.
- HTML 정적 검증과 워크플로 YAML 검증을 통과했다.

## 2026-05-10 GitHub token 브라우저 저장 옵션

- 사용자가 GitHub token을 매번 입력하지 않는 방식 중 브라우저 저장을 선택했다.
- Pages UI에 `이 브라우저에 토큰 저장` 체크박스와 `저장된 토큰 지우기` 버튼을 추가했다.
- 토큰은 `localStorage`의 `dhlottery.githubToken` 키에 저장한다.
- 체크박스를 끄거나 지우기 버튼을 누르면 저장된 토큰을 삭제한다.
- `python -m unittest discover -s tests` 결과 17개 테스트가 통과했다.
- HTML 정적 검증으로 localStorage 로드, 저장, 삭제 코드가 있는지 확인했다.

## 2026-05-10 카카오 알림 강제 재전송

- 사용자가 이미 보낸 1223회 결과를 카카오톡으로 다시 받기 위해 강제 재전송 체크박스를 요청했다.
- 단순히 `--no-state`를 쓰면 알림은 다시 가지만 새 결과를 상태 파일에 기록하지 않아 다음 자동 검사에서 중복 발송될 수 있다.
- 따라서 상태 파일은 읽고 저장하되 이번 실행의 알림 대상만 모든 해결된 결과로 바꾸는 `--force-notify` 옵션을 추가한다.
- Pages UI의 `강제 재전송` 체크박스는 `force_notify` workflow_dispatch 입력으로 전달된다.
- `저장 후 당첨 확인과 카카오 알림 실행`을 끄면 강제 재전송 체크박스도 자동으로 꺼지고 비활성화된다.
- `python -m unittest discover -s tests` 결과 18개 테스트가 통과했다.
- 워크플로 YAML 로딩 검증과 HTML 정적 검증을 통과했다.

## 2026-05-10 카카오 알림 문구 정리

- 사용자가 카카오톡 알림 내용이 지저분해 보여 한눈에 보는 요약과 구체적인 상세를 따로 받고 싶다고 요청했다.
- 기존 구현은 `_format_report`가 모든 결과 문장을 한 메시지로 이어 붙이고, `send_kakao_text`가 길이 제한에 따라 다시 쪼개는 방식이다.
- 새 구현은 검사 결과를 요약용 짧은 결과와 상세용 맞은 번호 설명으로 나누고, 카카오 발송 시 요약 메시지와 상세 메시지를 순서대로 보낸다.
- 요약 메시지는 게임 수, 당첨 수, 미당첨 수, 최고 일치 개수 또는 당첨 항목만 보여준다.
- 상세 메시지는 회차별 당첨번호와 각 게임의 맞은 번호, 보너스 일치 여부를 보여준다.
- `python -m unittest discover -s tests` 결과 19개 테스트가 통과했다.
- `data/tickets.example.yml` dry-run으로 요약과 상세가 분리되어 출력되는 것을 확인했다.
- `e9aef9c` 커밋을 원격 `main`에 푸시했다.

## 2026-05-10 로또 당첨 요약과 연금복권 입력 분리

- 사용자가 당첨된 항목이 있으면 첫 요약 메시지에서 로또 A-E 중 어떤 슬롯이 몇 등인지 보이길 원했다.
- 사용자가 입력 페이지에서 로또와 연금복권이 헷갈리지 않도록 잘 구분되길 원했다.
- 웹 입력 페이지는 정적 HTML이므로 기존 저장 워크플로는 그대로 두고, 브라우저에서 생성하는 YAML에 `lotto`와 `pension` 섹션을 함께 만들기로 한다.
- 연금복권 입력은 회차, 조, 6자리 번호를 별도 탭에서 입력하고 목록에 추가하는 방식으로 구현한다.
- 사용자가 제시한 연금복권 붙여넣기는 `315회` 아래 `1조`부터 `5조`까지 있고 각 조마다 숫자 6개가 한 줄씩 나뉜 형태다.
- Pages 파서는 각 조 아래 숫자를 이어 붙여 `052414`처럼 6자리 번호로 저장한다.
- 기본 로또 예시값은 연금복권만 입력할 때 섞이지 않도록 비워두었다.
- `python -m unittest discover -s tests` 결과 20개 테스트가 통과했다.
- Node DOM 모의 검증으로 연금복권 붙여넣기 샘플이 `group: 1`부터 `group: 5`, `number: "052414"` 5개로 YAML에 들어가는 것을 확인했다.
- `0d9f99e` 커밋을 원격 `main`에 푸시했다.

## 2026-05-10 다크모드와 동행복권 조회 실패 안정화

- 사용자가 GitHub Actions 로그에서 동행복권 로또 API 조회가 `TimeoutError`로 실패한 것을 공유했다.
- 실패 URL은 `https://www.dhlottery.co.kr/lt645/selectPstLt645InfoNew.do?srchDir=center&srchLtEpsd=1224`이고, 네트워크 시간 초과가 `HttpError`로 올라온 뒤 runner에서 잡히지 않아 작업이 실패했다.
- HTTP GET에는 재시도를 추가하고, 결과 조회 단계에서 끝까지 실패하면 “결과 조회 실패. 다음 실행에서 다시 시도합니다.”라는 미해결 결과로 처리한다.
- 미해결 결과는 중복 알림 상태에 저장하지 않으므로 다음 스케줄 또는 수동 실행에서 다시 확인된다.
- 입력 페이지에는 `다크모드` 토글을 추가하고 선택값을 `localStorage`의 `dhlottery.theme`에 저장한다.
- `python -m unittest discover -s tests` 결과 22개 테스트가 통과했다.
- Node DOM 모의 검증으로 다크모드 토글 저장과 연금복권 붙여넣기 파싱이 함께 동작하는 것을 확인했다.

## 2026-05-10 연금복권 회차 붙여넣기 보강

- 사용자가 `314회`로 시작하는 연금복권 붙여넣기에서 회차 자동 입력이 되지 않는다고 보고했다.
- 기존 `parsePensionRound`는 전체 텍스트에서 `회`를 찾은 뒤, 실패하면 숫자만 있는 줄만 회차로 인정했다.
- 복사 경로나 실행 환경에서 `회` 문자가 흔들리면 `314회` 첫 줄도 fallback에 걸리지 않을 수 있다.
- 첫 줄에 포함된 1~5자리 숫자를 우선 회차로 인식하도록 보강한다.
- 추가로 `1조`가 나오기 전까지의 줄에서 날짜나 시간 줄을 건너뛰고 회차 후보를 찾도록 보강한다.
- 초기화 버튼을 누른 뒤 사용자가 준 `314회` 샘플을 연금복권 붙여넣기에 넣는 DOM 모의 검증을 추가로 실행했고, `pensionRound`가 `314`로 채워지는 것을 확인했다.

## 2026-05-10 결과 요약 메시지 간소화

- 사용자가 카카오 요약 메시지를 `[동행복권 결과 요약]` 헤더와 회차별 `당첨 n개, 미당첨 n개` 형식으로 줄이길 요청했다.
- 기존 요약의 `N게임 중`, `최고 일치 n개` 문구는 제거한다.
- 전체 당첨이 0개일 때 `이번 회차는 당첨 없음.`을 마지막에 한 번만 붙인다.
- `python -m unittest discover -s tests` 결과 23개 테스트가 통과했다.
- `data/tickets.example.yml` dry-run으로 새 대괄호 헤더와 회차별 간소화 요약 출력을 확인했다.

## 2026-05-10 결과 확인 링크 추가

- 사용자가 카카오 메시지에서 동행복권 결과 사이트로 바로 이동할 수 있는 링크를 원했다.
- 요약 메시지 끝에 `결과 확인` 섹션을 추가하고, 게임별 공식 결과 페이지 URL을 본문에 넣는다.
- 로또는 `https://www.dhlottery.co.kr/lt645/result`, 연금복권은 `https://www.dhlottery.co.kr/pt720/result`를 사용한다.
- `python -m unittest discover -s tests` 결과 23개 테스트가 통과했다.
- `data/tickets.example.yml` dry-run으로 요약 메시지에 로또와 연금복권 결과 링크가 포함되는 것을 확인했다.

## 2026-05-10 결과 링크 배치 정리

- 사용자가 요약 줄을 먼저 공지하고, 그 아래에 로또와 연금복권 링크만 붙는 형식을 원했다.
- `이번 회차는 당첨 없음.`과 `결과 확인` 문구는 제거한다.
- 당첨 항목이 있는 경우에도 회차별 당첨/미당첨 요약을 먼저 보여주고 당첨 상세 줄은 그 뒤에 둔다.
- `python -m unittest discover -s tests` 결과 23개 테스트가 통과했다.
- `data/tickets.example.yml` dry-run으로 요약 블록, 당첨 상세 줄, 빈 줄, 링크 순서가 맞는지 확인했다.

## 2026-05-10 미발표 회차 알림 안내

- 사용자가 실제 구매 회차를 넣었을 때 아직 발표 전이면 페이지 오류처럼 보이지 않고 메시지에 발표 전이라고 알려주길 원했다.
- 기존에는 미해결 결과가 출력되지만 카카오 발송 조건이 해결된 결과에만 묶여 있어 발표 전 안내가 발송되지 않았다.
- `ResultNotReady`로 만든 미해결 결과는 카카오 발송 대상에 포함하고, `HttpError` 조회 실패는 기존처럼 출력만 하고 다음 실행에서 재시도하게 유지했다.
- 발표 전 메시지는 `[동행복권 결과 요약]`, 회차별 `아직 당첨결과 발표 전입니다.`, 결과 페이지 링크, 발표 후 재검사 안내 순서로 보낸다.
- `python -m unittest discover -s tests` 결과 25개 테스트가 통과했다.

## 2026-05-10 1분 초과 조회를 발표 전으로 처리

- 사용자가 아직 발표 전인 실제 구매 회차 조회에서 대기 시간이 너무 길다고 보고했고, 1분을 넘기면 발표 전으로 판단하길 원했다.
- 기존 HTTP GET은 기본 20초 타임아웃을 최대 3번 시도해서 전체 대기 시간이 약 1분을 넘을 수 있었다.
- `HttpTimeoutError`를 추가해 1분 제한을 넘긴 타임아웃을 일반 `HttpError`와 구분했다.
- 로또와 연금복권 결과 조회에서 `HttpTimeoutError`는 `결과 대기 중입니다`로 변환해 카카오의 발표 전 안내 대상에 포함한다.
- 일반 `HttpError`는 계속 `결과 조회 실패. 다음 실행에서 다시 시도합니다`로 남기며 카카오 알림은 보내지 않는다.
- `python -m unittest discover -s tests` 결과 27개 테스트가 통과했다.

## 2026-05-10 생성 결과 복원

- 사용자가 GitHub Pages 입력 화면의 `생성 결과` 영역에 저장된 로또와 연금복권 목록, YAML이 계속 표시되길 원했다.
- 기존 페이지는 현재 브라우저 입력값으로만 생성 결과를 만들어서 새로고침하면 저장된 GitHub 티켓 내용을 다시 보여주지 못했다.
- 생성된 YAML을 `localStorage`의 `dhlottery.ticketYaml`에 저장하고, 초기화 버튼을 누르면 이 캐시를 지운다.
- 페이지 로드 시 `https://raw.githubusercontent.com/asher8554/DHLottery/main/data/tickets.yml`을 읽어 로또와 연금복권 목록을 파싱한 뒤 기존 생성 결과 렌더링 흐름으로 복원한다.
- 사용자가 이미 입력을 시작했다면 늦게 도착한 원격 데이터가 화면을 덮어쓰지 않도록 `userEdited` 플래그를 둔다.
- Node 스크립트 구문 검사와 저장 YAML 복원 모의 검증을 통과했고, `python -m unittest discover -s tests` 결과 27개 테스트가 통과했다.

## 2026-05-10 결과 발표 후 구매번호 초기화

- 사용자가 카카오톡으로 실제 당첨 결과 발표가 정상 발송되면 생성 결과를 초기화하고, 발표 전이면 저장된 구매번호를 유지해 발표일 공지를 받길 원했다.
- `dhlottery_checker check`에 `--status-json` 옵션을 추가해 해결 결과 수, 미해결 결과 수, 실제 발송 수, 구매번호 초기화 권장 여부를 파일로 남긴다.
- `clear_tickets`는 해결된 결과 알림을 1건 이상 정상 발송했고 미해결 결과가 하나도 없을 때만 `true`가 된다.
- `update-ticket.yml`과 `check-results.yml`은 이 상태 파일을 읽어 `clear_tickets`가 true일 때만 `data/tickets.yml`을 빈 파일로 커밋한다.
- `check-results.yml`은 티켓 파일이 비어 있으면 스케줄 실행을 조용히 건너뛰도록 바꿔 초기화 뒤 불필요한 실패를 막았다.
- Pages는 원격 `data/tickets.yml`이 비어 있으면 브라우저에 저장된 생성 결과 캐시도 삭제하고 화면을 비운다.
- `python -m unittest discover -s tests` 결과 29개 테스트가 통과했고, HTML 스크립트 구문 검사와 원격 빈 파일 캐시 삭제 모의 검증, workflow YAML 파싱을 확인했다.

## 2026-05-10 연금복권 숫자 잡문자 보정

- 사용자가 연금복권 붙여넣기에서 `1조` 마지막 숫자가 `4wj`로 들어간 샘플을 줬고, 생성 결과에서 1조가 빠지는 문제를 보고했다.
- 기존 `parsePensionBlockTickets`는 조 블록 안에서 한 자리 숫자 줄 또는 6자리 숫자 줄만 인정했다.
- `4wj` 줄은 숫자 4로 시작하지만 뒤에 잡문자가 붙어 인정되지 않았고, 1조 블록은 5자리만 모인 상태에서 2조를 만나 누락됐다.
- 조 블록 안에서는 `^(\d)\D*$` 형태의 줄을 한 자리 숫자로 인정하도록 보정했다.
- Node 모의 검증으로 `4wj`가 들어간 315회 샘플에서 1조부터 5조까지 5개 티켓이 생성되고, 1조 번호가 `052414`가 되는 것을 확인했다.
- HTML 스크립트 구문 검사와 `python -m unittest discover -s tests` 결과 29개 테스트가 통과했다.

## 2026-05-10 로컬 구매내역 스크래퍼 추가

- 사용자가 동행복권 사이트에서 직접 내용을 복사하는 대신, 로그인 후 구매/당첨내역에서 현재 입력할 내용을 로컬 프로그램이 가져오길 원했다.
- 보안 방향은 계정 정보를 코드나 환경 파일에 저장하지 않고, Playwright가 띄운 로컬 Chromium에서 사용자가 직접 로그인하는 방식으로 정했다.
- `.browser/dhlottery` 프로필에 로그인 세션만 로컬 저장하며 `.gitignore`에 `.browser/`를 추가했다.
- `dhlottery_checker ticket_import`에 연금복권 파서와 로또/연금복권 통합 저장 함수를 추가했다.
- `scrape-ledger` CLI와 `scripts/scrape-ledger.ps1`을 추가해 구매/당첨내역의 티켓 보기 버튼을 찾아 텍스트를 수집하고 `data/tickets.yml`을 갱신한다.
- Playwright는 실행 시에만 import해 일반 당첨 확인과 테스트가 브라우저 설치에 의존하지 않도록 했다.
- `python -m unittest discover -s tests` 결과 34개 테스트가 통과했고, `python -m dhlottery_checker scrape-ledger --help`도 확인했다.

## 2026-05-10 로그인 직후 구매내역 이동 안정화

- 사용자가 `scrape-ledger.ps1` 실행 후 로그인하고 Enter를 눌렀을 때 구매내역 이동이 `loginSuccess.do?returnUrl=/main` 리다이렉트와 충돌하는 Playwright 오류를 보고했다.
- 원인은 로그인 성공 처리 페이지가 아직 자체 navigation 중인데 곧바로 `mypage/mylotteryledger`로 `goto`를 호출한 것이다.
- 로그인 후 Enter를 누르면 `domcontentloaded`와 `networkidle`을 기다리고 짧게 대기하는 `_wait_for_page_settle`을 추가했다.
- 구매내역 URL 이동 중 `interrupted by another navigation` 오류가 나면 페이지 안정화를 다시 기다린 뒤 최대 3번 재시도한다.
- 재시도가 모두 실패하면 traceback 대신 `구매내역 가져오기 실패` 경로로 사용자 메시지가 나오도록 `RuntimeError`를 발생시킨다.
- `python -m unittest discover -s tests` 결과 35개 테스트가 통과했고, `scrape-ledger --help`도 확인했다.

## 2026-05-10 로컬 env 로그인과 스크래퍼 디버그

- 사용자가 수동 로그인 후 구매내역 화면까지 갔지만 `구매내역에서 로또 또는 연금복권 티켓 번호를 찾지 못했습니다` 메시지를 받았다.
- 사용자는 아이디는 이미 채워져 있고 비밀번호는 로컬 `.env` 파일에 둘 테니 그것으로 로그인되길 요청했다.
- `.env`에서 `DHLOTTERY_PASSWORD` 또는 `DHLOTTERY_PW`를 읽고, 필요하면 `DHLOTTERY_ID`, `DHLOTTERY_USERNAME`, `DHLOTTERY_USER`도 읽도록 했다.
- `.env` 파일은 기존 `.gitignore`에 포함되어 있으므로 저장소에는 커밋하지 않는다.
- 로그인 폼이 보이면 비밀번호를 채우고 로그인 버튼 또는 Enter로 제출한다.
- 자동 로그인이 실패하거나 비밀번호가 없으면 기존처럼 사용자가 브라우저에서 직접 로그인하고 Enter를 누르는 흐름을 유지한다.
- 티켓 버튼 탐지는 일반 텍스트 버튼뿐 아니라 iframe 안의 요소, 이미지 `alt`, `title`, `onclick`, `href`까지 확인하도록 넓혔다.
- 티켓 텍스트를 찾지 못하면 `.browser/debug/ledger-body.txt`에 모든 frame의 화면 텍스트를 저장하고 가능하면 `.browser/debug/ledger-page.png`도 저장한다.
- `python -m unittest discover -s tests` 결과 37개 테스트가 통과했고, `scrape-ledger --help`와 PowerShell 스크립트 문법 검증도 통과했다.

## 2026-05-10 로그인 페이지 직접 진입

- 사용자가 `.\scripts\scrape-ledger.ps1` 실행 시 스크립트가 직접 `https://www.dhlottery.co.kr/login`에 들어가 로그인하고, 이후 `https://www.dhlottery.co.kr/mypage/mylotteryledger`로 이동하길 요청했다.
- 기존 흐름은 동행복권 홈으로 들어간 뒤 로그인 폼이 있으면 자동 로그인하는 구조라, 홈 화면에서 로그인 폼이 보이지 않는 경우 자동 로그인이 시작되지 않을 수 있었다.
- 기본 로그인 URL을 `LOGIN_URL = "https://www.dhlottery.co.kr/login"`으로 추가했다.
- 비헤드리스 실행에서는 로그인 URL로 먼저 이동해 `.env` credential로 로그인 시도 후 구매/당첨내역 URL로 이동한다.
- 구매/당첨내역으로 이동했는데 여전히 로그인 폼이 보이면 한 번 더 자동 로그인을 시도하고, 그래도 실패하면 수동 로그인 안내를 유지한다.
- PowerShell 스크립트와 CLI에 `--login-url` 전달 경로를 추가해 로그인 URL이 바뀌어도 override할 수 있게 했다.

## 2026-05-10 로그인 비밀번호 입력 보정

- 사용자가 `.env`에 비밀번호를 넣었지만 로그인 페이지에서 비밀번호가 입력되지 않는다고 보고했다.
- 실제 동행복권 로그인 페이지 HTML을 확인하니 사용자 입력용 아이디는 `#inpUserId`, 비밀번호는 `#inpUserPswdEncn`, 로그인 버튼은 `#btnLogin`이다.
- 숨김 전송 필드 `#userId`, `#userPswdEncn`은 로그인 버튼 클릭 시 페이지 JS가 RSA 암호화 값을 넣는 곳이므로 자동 입력 대상이 아니다.
- 기존 selector는 `input[type='password']`처럼 넓은 후보를 먼저 보고, 같은 selector에서 첫 번째 요소만 검사해 숨김 또는 잘못된 요소를 만날 때 visible 입력칸을 놓칠 수 있었다.
- 실제 로그인 폼의 id와 class를 selector 앞순위에 두고, 같은 selector 안의 모든 후보 중 visible 요소를 찾도록 바꾼다.
- Playwright headless 확인에서 `#inpUserId`, `#inpUserPswdEncn`, `#btnLogin`이 각각 1개씩 있고 모두 visible임을 확인했다.
- `python -m unittest discover -s tests` 결과 39개 테스트가 통과했고, CLI 도움말과 PowerShell 스크립트 문법 검증도 통과했다.

## 2026-05-10 돋보기 상세 팝업과 1시간 뒤 결과 확인

- 사용자가 구매내역 목록의 초록색 돋보기 아이콘을 누르면 이전에 복사 붙여넣기했던 티켓 상세 내용이 나온다고 설명했다.
- 목록에는 구입일자와 추첨일자가 있고, 상세 팝업에는 로또 `로또6/45 티켓 보기`, 연금복권 `구매번호`와 실제 번호가 표시된다.
- 스크래퍼는 글자 버튼만 찾으면 초록 돋보기 아이콘을 놓칠 수 있으므로 `search`, `btn-search`, `돋보기`, `조회`류 label과 티켓 문맥이 함께 있는 요소도 상세 버튼 후보로 본다.
- 같은 페이지에 모달이 열리면 배경 목록 텍스트와 상세 팝업 텍스트가 섞일 수 있어, 클릭 전후 텍스트 차이로 새로 추가된 팝업 줄을 우선 파싱한다.
- 사용자는 동행복권 결과 반영이 발표 후 최대 1시간 걸릴 수 있다고 확인했고, 자동 카카오 알림도 약 1시간 뒤 확인으로 운영하길 원했다.
- 연금복권 스케줄은 한국시간 목요일 20시 10분, 로또 스케줄은 토요일 21시 45분으로 조정했다.
- `python -m unittest discover -s tests` 결과 41개 테스트가 통과했고, workflow YAML 3개와 `scrape-ledger --help` 검증도 통과했다.

## 2026-05-10 스크래퍼 진행 로그와 실패 디버그 보강

- 사용자가 `scrape-ledger.ps1` 실행 중 진행 중인지 알 수 있게 중간마다 가져온 정보를 표시하는 옵션을 요청했다.
- 같은 실행에서 `구매내역에서 로또 또는 연금복권 티켓 번호를 찾지 못했습니다` 오류가 다시 발생했다.
- `.browser/debug/ledger-body.txt`에는 로그인 상태와 구매/당첨내역 목록이 정상 표시되어 있었고, 로또 2건과 연금복권 5건의 목록 텍스트가 있었다.
- 본문 텍스트에는 초록 돋보기 아이콘의 DOM 속성이 나오지 않으므로, 실패 시 후보 버튼 라벨을 `.browser/debug/ledger-candidates.txt`에도 저장하도록 한다.
- `--verbose`와 PowerShell `-ShowProgress`를 추가해 로그인 페이지 이동, 구매내역 이동, 목록 감지 건수, 상세 버튼 후보 수, 상세 클릭 결과를 터미널에 출력한다.
- 돋보기 아이콘 후보 판정은 아이콘 자체의 `search`, `detail`, `view`류 라벨과 주변 구매내역 행 텍스트를 함께 확인하도록 바꿨다.
- `python -m unittest discover -s tests` 결과 43개 테스트가 통과했고, `scrape-ledger --help`, PowerShell 스크립트 문법, workflow YAML 검증도 통과했다.

## 2026-05-10 스크래퍼 상세 팝업 수집 보정

- 실제 구매내역 DOM에서 초록 돋보기 아이콘은 별도 버튼이 아니라 `span.whl-txt.barcd` 요소에 붙은 스타일이었다.
- `.barcd` 요소의 `data-index`는 0부터 6까지 있었고, 0부터 4는 연금복권 315회, 5와 6은 로또 1224회 구매번호였다.
- 로또 상세 팝업은 `#Lotto645TicketP`, 연금복권 상세 팝업은 보이는 `.popup-wrap.on`에서 전체 텍스트를 직접 읽는 방식이 안정적이었다.
- 팝업 닫기 버튼은 텍스트가 없는 `button#btn-pop-close`였으므로 텍스트 `X`를 찾는 방식으로는 닫히지 않았다.
- 실제 `.\scripts\scrape-ledger.ps1 -MaxTickets 10 -ShowProgress` 실행 결과 로또 5개와 연금복권 5개가 `data/tickets.yml`에 정상 생성되는 것을 확인했다.

## 2026-05-10 Pages 자동 연동 화면 정리

- 사용자는 수동 붙여넣기 입력이 더 이상 필요 없고, 로컬 스크래퍼가 만든 `data/tickets.yml` 내용이 Pages의 생성 결과에 바로 올라오기를 원한다.
- 브라우저에서 열린 GitHub Pages는 로컬 PC 프로그램을 직접 실행할 수 없으므로 연결 경로는 `로컬 scrape-ledger 실행`, `data/tickets.yml 커밋/푸시`, `Pages가 원격 data/tickets.yml 로드` 순서가 된다.
- 기존 `ticket-entry.html`은 이미 원격 `data/tickets.yml`을 읽는 기능이 있었지만 수동 입력 UI가 중심이라 사용자 흐름과 맞지 않았다.
- `docs/ticket-entry.html`은 수동 입력 탭과 붙여넣기 파서를 제거하고, 원격 `data/tickets.yml`을 읽어 생성 결과와 요약만 표시하는 화면으로 바꿨다.
- 로컬 자동 연동은 `scripts/scrape-ledger-and-push.ps1`이 담당한다. 이 스크립트는 기존 `scrape-ledger.ps1`을 실행한 뒤 `data/tickets.yml`만 커밋하고 원격에 푸시한다.
- Pages에서 당첨 검사를 바로 누를 수 있도록 `check-results.yml`에 `force_notify` workflow_dispatch 입력을 추가했다.
- Playwright로 `docs/ticket-entry.html`을 열어 원격 구매번호 YAML이 로드되고 `생성 결과`에 `lotto:`가 표시되는 것을 확인했다.

## 2026-05-10 스크래퍼 실행 경로 정리

- 사용자는 `.\scripts\scrape-ledger-and-push.ps1 -ShowProgress` 실행 흐름은 좋지만 구현 과정에서 불합리하거나 더 짧게 쓸 수 있는 코드가 없는지 점검을 요청했다.
- 기능 동작은 유지하고, PowerShell wrapper의 반복 exit code 체크와 `git diff --quiet` 처리만 정리한다.
- `git diff --quiet`는 변경이 있으면 exit code 1을 반환하므로 이 값은 오류가 아니라 커밋 진행 신호로 다뤄야 한다.
- `scrape-ledger.ps1`에도 UTF-8 콘솔 설정을 추가해 두 스크립트가 같은 인코딩 기준으로 동작하게 한다.
- Python 스크래퍼의 상세 버튼 CSS selector 문자열은 두 함수에서 중복되어 상수로 올렸다.

## 2026-05-10 예치금 Pages 동기화

- 사용자는 동행복권 메인 화면에서 현재 예치금을 확인하고, `https://asher8554.github.io/DHLottery/ticket-entry.html`에서도 같은 금액을 볼 수 있길 원한다.
- 예치금은 로그인 후에만 보이는 값이므로 GitHub Pages가 직접 동행복권 사이트를 조회하지 않고 로컬 스크래퍼가 읽은 스냅샷을 공개 파일로 커밋한다.
- 새 공개 파일은 `data/account.yml`로 둔다. 티켓 파일과 분리해 결과 발표 후 `data/tickets.yml`이 초기화되어도 마지막 예치금 스냅샷은 유지한다.
- 기존 로컬 실행 명령은 `.\scripts\scrape-ledger-and-push.ps1 -ShowProgress` 그대로 쓰고, 내부에서 티켓과 예치금 파일을 함께 커밋하도록 한다.
- 동행복권 메인 본문에서 바로 읽으면 `예치금 0원`이 먼저 잡힐 수 있었다. 실제 금액은 사용자가 보여준 초록색 전체메뉴 패널 안에 있으므로 `#goGnb`를 열고 그 패널의 예치금을 우선 사용한다.
- 실제 로컬 실행에서 예치금 `40,000원`을 확인했고 `data/account.yml`에 `balance.amount: 40000`으로 저장했다.

## 2026-05-10 예치금 부족 알림

- 사용자는 예치금이 50,000원 이하가 되면 50,000원을 자동 충전하고, `.env`의 간편비밀번호를 누르게 만들고 싶다고 요청했다.
- 실제 돈이 이동하는 충전 자동화와 간편비밀번호 자동 입력은 구현하지 않는다. 프로젝트의 기존 제외 범위인 예치금 충전 자동화와 금융거래 자동화에도 해당한다.
- 안전한 대체 흐름은 `data/account.yml` 스냅샷을 기준으로 예치금이 50,000원 이하이면 카카오톡 알림을 보내고, Pages에서 `충전 필요`를 표시하는 것이다.
- 알림은 GitHub Actions에서 `data/account.yml` 변경 시 실행한다. 충전 자체는 사용자가 동행복권에서 직접 확인하고 진행한다.
- 같은 예치금 금액에 대해서는 중복 카카오 알림을 막는다. 예치금이 더 줄어 다른 금액이 되면 다시 알림 대상이 된다.
- 현재 `data/account.yml` 기준 예치금은 40,000원이므로 Pages는 `충전 필요`를 표시한다.

## 2026-05-10 시놀로지 정기 실행 구성

- 사용자는 지금까지 만든 스크래퍼와 Pages 동기화 흐름을 시놀로지에서 매주 자동 실행하고 싶어 한다.
- 시놀로지 DSM 네이티브 환경은 Chromium 실행 의존성이 부족할 수 있으므로 Docker/Container Manager 방식이 더 안정적이다.
- Linux용 실행 래퍼는 기존 PowerShell 스크립트와 같은 역할을 하되, 기본값을 headless 실행으로 둔다.
- 주간 작업은 `scripts/synology-docker-run.sh`를 DSM 작업 스케줄러에서 호출하는 구조로 안내한다.
- Docker 이미지에는 Python 3.12, Git, SSH client, Playwright Chromium 의존성을 넣는다.
- `NO_PUSH=1` 같은 테스트 옵션이 컨테이너 안까지 전달되도록 `scripts/synology-docker-run.sh`에서 환경변수를 넘긴다.

## 2026-05-11 시놀로지 headless 예치금 조회 보정

- 시놀로지 로그에서 구매번호 수집은 성공했지만 예치금만 `찾지 못했습니다`로 출력됐다.
- 원인은 headless 실행에서 로그인 페이지 이동을 건너뛰고 메인 화면의 예치금을 먼저 읽은 뒤, 구매내역 페이지에서야 로그인 폼을 제출했기 때문이다.
- 해결은 headless에서도 로그인 페이지를 먼저 열어 자동 로그인을 시도하고, 구매내역에서 뒤늦게 로그인된 경우 메인으로 돌아가 예치금을 다시 읽는 것이다.
- 사용자의 실제 저장소 경로는 `/volume1/docker/Github/DHLottery`이므로 문서의 `/volume1/docker/DHLottery` 예시는 혼동을 줄이도록 함께 보강한다.
- 일반 사용자 계정은 Docker daemon socket 권한이 없어 `permission denied`가 났다. DSM 작업 스케줄러는 root로 실행하거나 사용자를 Docker 권한 그룹에 넣어야 한다.

## 2026-05-11 시놀로지 가이드 최종 정리

- 사용자가 문서의 우회 절차로 실제 문제를 해결했다고 알려줬다.
- `docs/synology-setup.md`는 더 이상 시도 순서가 섞이지 않도록 정상 흐름을 Docker 기준으로 재정렬한다.
- 기본 경로는 `/volume1/docker/Github/DHLottery`, 실행 사용자는 root, Git 명령은 컨테이너 기반으로 안내한다.
- 실패했던 `alpine/git`, `ssh-keyscan`, Docker socket 권한, pull rebase 충돌은 문제 해결 섹션에 모아둔다.
- 문서 검증으로 `git diff --check`를 실행했고, 전체 테스트는 `python -m unittest discover -s tests` 기준 55개가 통과했다.

## 2026-05-17 시놀로지 무알림 진단 보강

- 사용자는 SSH로 한 번 실행했지만 1주일 뒤 시놀로지 작업 스케줄은 도는 것 같은데 카카오톡 메시지가 오지 않는다고 했다.
- VS Code Remote-SSH 화면은 `192.168.35.131 port 22: Permission denied`로, 저장소 코드가 아니라 시놀로지 SSH 접근 자체가 막힌 상태로 보인다.
- `gh run list --workflow check-results.yml`로 확인한 결과 2026-05-16 23:08 KST 실행된 `Check lottery results`는 성공했다.
- 해당 실행 로그에는 `새로 알릴 결과가 없습니다.`와 `Keeping ticket file for a later result check.`가 있었다.
- 따라서 적어도 최근 결과 확인 워크플로 자체가 실패해서 카카오톡이 안 간 상황은 아니다. 새로 보낼 결과가 없다고 판단했거나 이미 보낸 상태 캐시가 복원된 가능성이 크다.
- `Check balance` 최근 실행은 push 이벤트로 성공했고 로그에 예치금 부족 메시지 본문이 출력되었다. 이 경우 카카오 API 호출은 성공한 것으로 보인다.
- 앞으로 원인 파악이 쉽도록 `check-results.yml`에 `.state/check-status.json` 내용을 출력하는 `Print check status` 단계를 추가했다.
- `docs/synology-setup.md`에 카카오톡 알림이 오지 않을 때 시놀로지 로그, Actions 로그, `Print check status`, 강제 재전송, Remote-SSH 확인 순서를 추가했다.
- `python -m unittest discover -s tests` 결과 55개 테스트가 통과했고, workflow YAML 4개 파싱을 확인했다.
- 시놀로지 무알림 진단 보강 커밋을 생성하고 원격에 푸시할 예정이다.

## 2026-05-17 Pages 카카오 알림 시간 설정

- 사용자는 GitHub 원격 내용을 현재 프로젝트에 반영한 뒤, GitHub Pages에서 카카오톡 메시지 발송 시간을 설정할 수 있기를 원한다.
- GitHub Pages는 정적 사이트라 workflow cron 자체를 안전하게 직접 수정하기 어렵다.
- 대신 `check-results.yml`을 짧은 주기로 실행하고, 저장소의 `data/notification-settings.yml` 설정이 현재 KST 시간과 맞을 때만 실제 당첨 검사를 수행하는 방식으로 설계한다.
- Pages 화면은 기존 GitHub fine-grained token을 사용해 `data/notification-settings.yml`을 GitHub Contents API로 저장한다.
- 이 토큰에는 기존 `Actions: Read and write` 외에 `Contents: Read and write` 권한이 필요하다.
- 스케줄 판정은 `dhlottery_checker.schedule_config`에서 표준 라이브러리만 사용하도록 구현했다.
- 예약 실행이 설정 시간 밖이면 Actions가 의존성 설치와 카카오 API 호출을 건너뛰도록 workflow 초반에 판정한다.
- 검증은 `python -m unittest discover -s tests`, workflow YAML 파싱, `docs/ticket-entry.html` 스크립트 문법 확인, `git diff --check`로 진행했다.
- 구현 커밋은 `ba9e41d`로 원격 `main`에 푸시했다.

## 2026-05-17 Pages 생성 결과 UI 정리와 시놀로지 운영 안내

- 사용자는 Pages의 생성 결과에 원본 YAML이 길게 노출되는 것이 불편하고, 색깔 공 표시가 당첨처럼 보일 수 있다고 피드백했다.
- 원본 YAML은 복사와 디버깅용으로는 쓸모가 있으므로 삭제하지 않고 기본 접힘 상태의 `원본 YAML 보기` 안으로 옮긴다.
- 색깔 공 표시는 실제 당첨 여부와 무관한 장식이므로 제거한다.
- 카카오 알림 시간 설정은 GitHub Actions가 결과를 확인하는 시간이고, 시놀로지 작업은 그 전에 구매내역을 `data/tickets.yml`로 올려두는 역할임을 문서에 분리해서 설명한다.
- 검증은 색깔 공 관련 코드 검색, `docs/ticket-entry.html` 스크립트 문법 확인, `python -m unittest discover -s tests`, `git diff --check`로 진행했다.
- 구현 커밋은 `b1790ea`로 원격 `main`에 푸시했다.

## 2026-05-17 Pages 알림 시간 저장 403 개선

- 사용자가 Pages에서 알림 시간 저장 시 `Resource not accessible by personal access token` 403을 만났다.
- 현재 구현은 GitHub Contents API로 `data/notification-settings.yml`을 직접 수정하므로 token에 `Contents: Read and write`가 없으면 실패한다.
- 사용자가 이미 `당첨 검사 실행`에 필요한 `Actions: Read and write` token을 쓰고 있으므로, 저장도 workflow dispatch로 처리하면 token 권한 요구를 줄일 수 있다.
- 새 workflow는 `workflow_dispatch` 입력을 검증한 뒤 GitHub Actions의 `GITHUB_TOKEN`과 `contents: write` 권한으로 설정 파일을 커밋한다.
- 검증은 Pages 스크립트 문법 확인, workflow YAML 파싱, 전체 unittest, `git diff --check`로 진행했다.
- 구현 커밋은 `db9496f`로 원격 `main`에 푸시했다.

## 2026-05-17 Pages 설정 영역 접기

- 사용자는 현재 저장된 알림 시간 값은 그대로 두고, 화면에 항상 보일 필요가 없는 설정성 정보만 접었다 펼칠 수 있기를 원한다.
- 대상은 로컬 스크래퍼 명령, GitHub token 및 수동 실행 영역, 카카오톡 알림 시간 설정 영역이다.
- 구매번호 요약과 상태값은 계속 기본 노출하고, 실제 조작이 필요한 설정만 `details`로 감춘다.
- `docs/ticket-entry.html`의 세 설정 영역을 `details.foldout`으로 감쌌고, 현재 저장된 `data/notification-settings.yml` 값은 변경하지 않았다.
- 검증은 Pages 스크립트 문법 확인, 전체 unittest, `git diff --check`로 진행했다.
- 원격에 먼저 들어온 `9020417 카카오 알림 시간 설정 갱신`을 `git pull --rebase`로 반영한 뒤 UI 커밋을 푸시했다.

## 2026-05-17 발표 시간 초기화 버튼

- 사용자는 현재 저장된 카카오톡 알림 시간은 그대로 두되, 설정 화면에서 발표 시간으로 되돌리는 버튼을 원한다.
- 동행복권 공식 안내 기준 추첨시간은 로또6/45 매주 토요일 20:35경, 연금복권720+ 매주 목요일 19:05경이다.
- 버튼은 폼 입력값만 발표 시간으로 바꾸고, 실제 `data/notification-settings.yml` 반영은 사용자가 `알림 시간 저장`을 눌렀을 때만 진행하게 한다.
- 검증은 Pages 스크립트 문법 확인, 전체 unittest, `git diff --check`로 진행했다.
- 구현 커밋은 `6ee8095`로 원격 `main`에 푸시했다.

## 2026-05-17 해결된 구매번호 부분 삭제

- 사용자는 연금복권 315회 결과가 이미 나왔는데 GitHub Pages에 계속 표시된다고 보고했다.
- 원인은 `check-results.yml`이 `clear_tickets=true`일 때만 `data/tickets.yml` 전체를 비우는 방식이었기 때문이다.
- 316회처럼 아직 pending인 항목이 있으면 `pending_count > 0`이라 315회 resolved 항목도 함께 남았다.
- 해결 방향은 결과가 확정되고 이미 알림 상태에 들어간 항목만 `data/tickets.yml`에서 부분 삭제하고, 아직 결과 대기인 항목은 보존하는 것이다.
- `check` 상태 JSON에 `removable_resolved_fingerprints`를 기록하고, `prune-sent-tickets` 명령이 해당 항목만 `data/tickets.yml`에서 제거하도록 구현했다.
- `check-results.yml`과 `update-ticket.yml`은 전체 초기화 대신 `prune-sent-tickets`를 호출하도록 바꿨다.
- 검증은 `python -m unittest discover -s tests`, workflow YAML 파싱, `git diff --check`로 진행했고 62개 테스트가 통과했다.
- 원격에 먼저 들어온 `105a36e 카카오 알림 시간 설정 갱신`을 rebase로 반영한 뒤 구현 커밋 `eb73301`을 푸시했다.

## 2026-05-17 발표 전 대기 알림 선택화

- 사용자는 발표 전 또는 결과 미반영 상태에서 "발표 후 다시 검사" 카카오톡 메시지가 기본 발송되지 않기를 원한다.
- 대기 알림은 사용자가 체크박스로 명시한 경우에만 발송되어야 한다.
- 기본값은 `notify_pending: false`로 두고, 결과가 확정된 항목의 당첨/미당첨 알림은 기존처럼 보낸다.
- `check` CLI에 `--notify-pending`을 추가했고, Pages와 Actions는 `notify_pending` 체크박스와 설정값을 이 옵션으로 전달한다.
- 검증은 전체 unittest 64개, workflow YAML 파싱, Pages 스크립트 문법 확인, `git diff --check`로 진행했다.
- 원격에 먼저 들어온 `7fbf2b8 구매번호 정리`를 rebase로 반영한 뒤 구현 커밋 `161edfd`를 푸시했다.

## 2026-05-17 당첨결과 이력 표시

- 사용자는 지난 당첨결과 요약을 GitHub Pages 안에서 쉽게 확인하고 싶어 한다.
- 이력에는 실제 구매번호를 저장하거나 표시하지 않고, 검사 날짜, 게임, 회차, 미당첨 개수, 당첨 등수 개수만 저장한다.
- 저장 파일은 `data/result-history.yml`로 둔다. `data/tickets.yml`은 발표 후 정리되므로 과거 이력을 별도 파일로 남겨야 Pages에서 이전 결과를 볼 수 있다.
- 같은 게임과 회차가 다시 검사되면 새 줄을 추가하지 않고 기존 이력 항목을 교체해 중복 표시를 막는다.
- `check-results.yml`과 `update-ticket.yml`은 검사 직후 `--history data/result-history.yml`을 넘기고, 구매번호 정리 커밋에 이력 파일도 함께 포함한다.
- Pages는 `data/result-history.yml`을 원격 raw URL로 읽어 `지난 당첨결과 이력` 접힘 영역에 최대 20건을 표시한다.
- 검증은 전체 unittest 66개, workflow 및 data YAML 파싱, Pages 스크립트 문법 확인, `git diff --check`로 진행했다.
- 구현 커밋은 `a3c121b`이다.

## 2026-05-17 생성 결과 로또 회차 표시

- 사용자는 Pages의 생성 결과에서 로또 구매번호에도 회차가 보이길 원한다.
- 기존 연금복권 줄은 `316회 1조 ...`처럼 회차가 보였지만 로또 줄은 `로또 A`처럼 슬롯만 보여 회차 확인이 어려웠다.
- `docs/ticket-entry.html`의 `renderTickets`에서 로또 슬롯을 `로또 {round}회 {slot}` 형태로 표시한다.
- 당첨결과 이력 보존 흐름을 다시 확인했다. `_run_check`가 `data/result-history.yml`을 먼저 갱신하고, workflow의 이후 단계가 완료된 구매번호만 `data/tickets.yml`에서 정리한 뒤 두 파일을 함께 커밋한다.
- 검증은 Pages 스크립트 문법 확인, 전체 unittest 66개, workflow YAML 파싱, `git diff --check`로 진행했다.

## 2026-05-22 Ouroboros setup

- `ooo setup`은 현재 Codex 세션에서 요청되었으므로, setup skill의 안내에 따라 Claude Code 내장 wizard 대신 `ouroboros setup --runtime codex` CLI 경로를 사용한다.
- 로컬 환경에는 `ouroboros.exe`, `uvx.exe`, Python 3.13.7, Python 3.12.8이 모두 있어 setup 실행 전제 조건은 충족된 것으로 보인다.
- `ouroboros setup --runtime codex` 실행 결과 Codex runtime 설정이 완료되었고, 설정은 `C:\Users\asher\.ouroboros\config.yaml`에 저장되었다. Codex rules와 20개 Ouroboros skills 설치 메시지도 확인했다.
- 검증 결과 `runtime_backend: codex`, `backend: codex`, Codex skill directory 21개, `Ouroboros version 0.39.0`을 확인했다.

## 2026-05-22 Pages 당첨 결과 상세 표시

- 사용자는 Pages에서 당첨 결과도 같이 확인할 수 있기를 원한다.
- 현재 Pages는 `data/tickets.yml` 구매번호와 `data/result-history.yml`의 짧은 요약만 보여준다.
- 브라우저에서 동행복권 API를 직접 호출하는 방식은 CORS와 외부 사이트 변경에 취약하므로 기존 GitHub Actions 검사 결과를 `data/result-history.yml`에 더 풍부하게 저장하는 방향을 택한다.
- 이력 파일에는 공개 당첨번호와 티켓별 결과 라벨만 저장하고, 구매번호 원문 전체는 저장하지 않는다.
- 기존 카카오 알림, 중복 알림 상태, 완료 구매번호 정리 흐름은 그대로 유지한다.
- 기준 baseline은 `python -m unittest discover -s tests` 66개 통과 상태다.
- 구현 후 결과 이력에는 `winning`과 `tickets` 필드가 추가된다. 로또는 당첨번호 6개와 보너스 번호를 저장하고, 연금복권은 조, 당첨번호, 보너스 번호를 저장한다.
- `tickets` 항목은 라벨, 당첨 여부, 결과 라벨, 로또 일치 개수만 저장한다.
- Pages는 기존 한 줄 이력을 결과 카드로 렌더링하고, 기존 이력처럼 새 필드가 없는 항목도 요약만 표시할 수 있게 유지한다.
- 검증은 새 unittest 포함 전체 68개 통과, UTF-8 파일 직접 읽기 방식의 inline script 문법 검사, `git diff --check`로 진행했다.
- PowerShell 파이프로 script를 Node에 넘긴 문법 검사는 한글 정규식의 `회`가 `?`로 깨져 실패했다. 파일을 UTF-8로 직접 읽는 방식에서는 통과하므로 코드 문제가 아니라 검증 명령의 인코딩 문제로 판단했다.

## 2026-05-22 예약 실행 대상 복권 제한

- 사용자는 프로그램 전반의 리팩터링과 보완점을 살펴보고 고치길 원한다.
- baseline은 깨끗했다. 작업 시작 시 `git status --short`는 출력이 없었고, `python -m unittest discover -s tests`는 68개 통과였다.
- 가장 직접적인 보완점은 `schedule_config`가 `due_games`를 계산하지만 `.github/workflows/check-results.yml`의 실제 검사 명령이 항상 전체 검사로 실행되는 점이다.
- 로또 예약 시간에 연금복권 pending 또는 결과까지 같이 처리될 수 있으므로, 예약 실행에서는 도래한 게임 하나만 `--game`으로 넘기도록 보완한다.
- 수동 실행은 사용자가 명시적으로 누른 검사이므로 기존처럼 전체 검사를 유지한다.
- `check-results.yml`의 검사 단계에 `DUE_GAMES` 환경값을 추가하고, 예약 실행에서 `lotto` 또는 `pension` 단일 값일 때만 `--game` 인자를 해당 값으로 바꾸도록 했다.
- `due_games`가 `lotto,pension`처럼 복수이거나 수동 실행이면 `--game all`을 유지한다.
- 새 테스트 `tests/test_workflows.py`는 workflow가 `due_games` output을 읽고 `--game "$game_arg"`를 넘기는 계약을 확인한다.
- 검증은 focused workflow 테스트, 전체 unittest 69개, workflow YAML 파싱, `git diff --check`로 진행했다.

## 2026-05-24 Ouroboros setup refresh

- User requested `ooo setup` in a Codex desktop session.
- Assumption: refresh/verify the existing Codex setup rather than run the Claude Code-only wizard flow.
- The setup skill says standalone Codex users should use `ouroboros setup --runtime codex`; this run will prefer that path and verify the resulting config/skills.
- Initial setup rerun failed because Windows CP949 output could not encode Rich's Unicode checkmark. Minimal reproduction was `python -c "print('✓')"`.
- Rerun succeeded with `PYTHONUTF8=1` and `PYTHONIOENCODING=utf-8`.
- Verified `C:\Users\asher\.ouroboros\config.yaml` has `runtime_backend: codex` and `backend: codex`.
- Verified `C:\Users\asher\.codex\config.toml` contains the Ouroboros MCP server and task profiles.
- Verified 20 `ouroboros-*` Codex skills are installed and `ouroboros --version` reports 0.39.0.

## 2026-05-24 Pages 동행복권 바로가기

- 사용자는 GitHub Pages 화면에서 동행복권 사이트로 한 번에 이동할 수 있는 버튼을 원했다.
- 대상 주소는 `https://www.dhlottery.co.kr/`다.
- 기존 Pages 화면은 `docs/ticket-entry.html`이며, 외부 이동은 새 탭 링크 패턴을 이미 사용한다.
- 구현은 상단 액션 영역에 바로가기 링크를 버튼처럼 보이게 추가하는 방향으로 한정한다.
- 테스트는 `tests/test_pages.py`에 링크 문구와 정확한 href를 확인하는 방식으로 추가했다.
- 검증은 `python -m unittest tests.test_pages`, `python -m unittest discover -s tests`, `git diff --check`, Node inline script syntax check로 진행했다.
- 브라우저 확인은 Codex 앱 보안 정책상 `file://` URL 열기가 차단되어 생략했다.

## 2026-05-24 Pages 스크래퍼 실행 상태 표시

- 사용자는 Pages UI에서 시놀로지 작업 스케줄러가 로컬 스크래퍼를 실행했는지 쉽게 확인하고 싶어 한다.
- 현재 Pages는 `data/account.yml`의 `updated_at`을 예치금 갱신 시각으로만 보여주므로, 스크래퍼 성공 여부를 한눈에 보기 어렵다.
- 기존 스크래퍼는 시놀로지와 Windows 수동 실행 모두 성공 시 `data/account.yml`과 `data/tickets.yml`을 같이 갱신한다.
- 별도 실행 출처 필드가 없으므로, 이번 UI는 "시놀로지 전용 여부"가 아니라 "스크래퍼 마지막 반영 시각"을 명확히 보여주는 방향으로 한정한다.
- 최초 구현은 24시간 이내 갱신을 `성공`, 그보다 오래된 갱신을 `확인 필요`로 표시했다.
- 사용자는 발표 전 로또나 연금복권 구매번호가 남아 있는 경우 추가 스크래퍼 실행이 필요한 것처럼 보이면 안 된다고 정정했다.
- 따라서 `updated_at`이 정상 값이면 시간 경과와 발표 대기 여부에 상관없이 `성공`으로 표시하고, 값이 없거나 형식이 깨진 경우만 `미확인`으로 둔다.
- 접힘 영역에는 Windows 수동 명령과 DSM 작업 스케줄러 명령을 모두 노출해 사용자가 시놀로지 쪽 실행 경로를 바로 확인할 수 있게 한다.
- 검증은 `python -m unittest discover -s tests`, `git diff --check`, 로컬 Pages 브라우저 렌더링 확인으로 진행했다.
- 브라우저 확인 결과 `스크래퍼 실행 성공 · 2026. 5. 24. 오후 2:56:41`과 시놀로지, Windows 스크래퍼 명령 2개가 표시되었다.
- 경고 제거 후 검증은 전체 unittest 73개 통과, `git diff --check` 통과, 브라우저에서 `pageHasCheckNeeded: false`와 `scraper-status good` 확인으로 진행했다.

## 2026-05-24 Pages 시놀로지 스크래퍼 출처 표시

- 사용자는 DSM 작업 스케줄러를 실행했을 때 GitHub Pages에서 시놀로지가 실제로 실행됐는지 확인하고 싶어 한다.
- 기존 Pages 표시 방식은 `data/account.yml`의 `updated_at`만 사용하므로 Windows 수동 실행과 시놀로지 자동 실행을 구분할 수 없다.
- 해결 방향은 스크래퍼 push 스크립트가 `data/scraper-status.yml`에 `source`, `source_label`, `updated_at`을 기록하고, Pages가 이 파일을 우선 읽어 실행 출처를 표시하는 것이다.
- 상태 파일이 아직 없는 배포나 fetch 실패 상황에서는 기존처럼 `data/account.yml`의 갱신 시각으로 일반 성공 상태를 표시하도록 fallback을 유지한다.
- `scripts/synology-docker-run.sh`는 Docker 컨테이너에 `SCRAPER_SOURCE=synology`를 기본값으로 전달한다.
- Windows 수동 실행 스크립트는 기본값을 `windows`로 둬서 로컬 수동 실행과 DSM 자동 실행이 Pages에서 구분되게 했다.
- 새 상태 파일은 데이터 변경이 없더라도 실행 시각이 바뀌므로, 시놀로지 작업이 정상 push되면 Pages에서 마지막 실행을 확인할 수 있다.
- 검증은 실패 테스트 확인 후 전체 unittest 75개 통과, Bash 문법 검사, PowerShell scriptblock 파싱, Pages inline script 구문 검사, `git diff --check`로 진행했다.
- 로컬 브라우저 검증에서는 `data/scraper-status.yml` 응답을 `source: synology`로 제공했을 때 `시놀로지 실행 성공 · 2026. 5. 24. 오전 9:00:00`과 `scraper-status good` 클래스를 확인했다.

## 2026-05-24 시놀로지 Git 상태 복구 보강

- 시놀로지에서 최신 코드로 전환한 뒤 스크래퍼가 `data/scraper-status.yml`을 만들고 커밋 `1388748 구매번호 자동 반영`을 push했다.
- GitHub 원격의 `data/scraper-status.yml`은 `source: "synology"`, `source_label: "시놀로지 실행"`, `updated_at: "2026-05-24T07:30:37Z"`로 확인됐다.
- GitHub 원격의 `data/account.yml`도 `updated_at: "2026-05-24T07:30:36Z"`로 같은 실행 흐름을 가리킨다.
- 이 PC에서 `ssh asher8554@192.168.35.131`은 `Permission denied (publickey,password)`로 실패했다. 직접 SSH 점검을 하려면 Windows 쪽 SSH 키 설정이 필요하다.
- 재발 원인은 이전 시놀로지 저장소가 detached HEAD와 남은 rebase 상태를 가지고 있었고, 스크립트가 스크래핑 후에야 `git pull --rebase`를 실행해 push 단계에서 멈춘 점이다.
- `scripts/scrape-ledger-and-push.sh`는 이제 스크래핑 전에 rebase 잔여 상태를 확인하고, 현재 브랜치가 아니면 `main`으로 전환한 뒤 `git pull --rebase origin main`을 먼저 실행한다.
- 스크래핑 후에도 `git pull --rebase origin main`, `git push origin main`처럼 대상 브랜치를 명시해 upstream 설정에 덜 의존하게 했다.

## 2026-05-24 Pages 스크래퍼 상태 캐시 회피

- 사용자는 Pages에서 여전히 `시놀로지 실행 성공` 시간이 16:30으로 보인다고 보고했다.
- GitHub API의 `data/scraper-status.yml`은 `updated_at: "2026-05-24T07:50:47Z"`로 최신이지만, `raw.githubusercontent.com` URL은 같은 시점에 `updated_at: "2026-05-24T07:30:37Z"`를 반환했다.
- 원인은 Pages가 raw URL을 읽고 있고, GitHub raw 캐시가 최신 커밋보다 늦게 갱신되는 상황으로 판단했다.
- 해결은 `data/scraper-status.yml`만 GitHub Contents API를 우선 사용해 읽고, API 실패 시에만 기존 raw URL로 fallback하는 방식으로 한정한다.
- 검증은 Pages 계약 테스트 포함 전체 unittest 76개 통과, HTML inline script 구문 검사 통과, `git diff --check` 통과, GitHub Contents API가 최신 `updated_at: "2026-05-24T07:50:47Z"`를 반환하는 것으로 진행했다.

## 2026-05-24 결과 이력 중복 구매번호 정리

- 사용자는 지난 당첨결과 이력에 연금복권 316회가 있는데 생성 결과에도 316회가 다시 보인다고 보고했다.
- 현재 데이터 확인 결과 `data/result-history.yml`에는 연금복권 316회 완료 이력이 있고, `data/tickets.yml`에도 연금복권 316회 구매번호 5개가 남아 있었다.
- 원인 후보는 스크래퍼가 동행복권 구매내역의 과거 구매를 다시 가져오면서, 기존 결과 이력에 이미 완료된 회차를 가져온 뒤 정리하지 않는 흐름이다.
- 해결 방향은 `prune-sent-tickets`가 상태 JSON의 알림 완료 fingerprint뿐 아니라 `data/result-history.yml`의 완료 회차도 제거하게 하고, 스크래퍼 push 흐름과 GitHub Actions 모두 이 기준 정리를 호출하게 하는 것이다.
- 구현 후 `python -m dhlottery_checker prune-sent-tickets --tickets data/tickets.yml --status-json .state/check-status.json --history data/result-history.yml`로 연금복권 316회 구매번호 5개를 제거했다.
- 검증은 focused 실패 테스트 확인 뒤 전체 unittest 79개 통과, `bash -n`, PowerShell scriptblock 파싱, `git diff --check` 통과로 진행했다.

## 2026-05-24 결과 이력 티켓 배지 라벨 개선

- 사용자는 결과 이력 티켓 배지를 `연금 1 | 7등 1천원`, `로또 1 | 몇등 얼마`처럼 게임 종류와 순번이 더 명확한 형태로 보이길 원한다.
- 기존 Pages 배지는 `.history-ticket-number`와 `.history-ticket-result`를 분리해 세로 구분선을 이미 제공하고 있었다.
- 이번 변경은 배지 구조와 색상은 유지하고, 왼쪽 라벨 계산만 게임 축약명 포함 형태로 바꾸는 범위로 제한한다.
- 구현은 `historyTicketBadgeLabel`을 추가해 `pension`은 `연금`, `lotto`는 `로또` 접두어를 붙이고, 배지 왼쪽 영역의 최소 폭과 줄바꿈 방지를 조정했다.
- 검증은 focused Pages 테스트 실패 확인 뒤 전체 unittest 80개 통과, HTML inline script 구문 검사 통과, `git diff --check` 통과, Playwright 렌더 확인으로 진행했다.

## 2026-05-24 연금 결과 배지 한 줄 표시

- 사용자는 지난 당첨결과 이력 카드에서 연금 1~5 배지가 4개와 1개로 줄바꿈되는 점을 보고, 1~5가 한 줄에 보이도록 간격 조정을 요청했다.
- 기존 `.history-ticket-list`는 flex wrap과 6px gap을 쓰고 있어 카드 폭과 배지 텍스트 폭에 따라 5번째 배지가 다음 줄로 내려갈 수 있다.
- 해결 방향은 티켓이 5개인 결과 이력 리스트에만 전용 클래스를 붙여 데스크톱에서 5열 grid로 배치하고, 좁은 화면에서는 자동 줄바꿈되게 유지하는 것이다.
- 구현은 5개 티켓 리스트에 `history-ticket-list five-up` 클래스를 붙이고, 데스크톱에서는 `repeat(5, minmax(0, 1fr))` grid를 사용하게 했다.
- 검증은 focused 실패 테스트 확인 뒤 전체 unittest 81개 통과, HTML inline script 구문 검사 통과, `git diff --check` 통과, Playwright에서 5개 배지의 top 좌표가 같은 것을 확인하는 방식으로 진행했다.

## 2026-05-24 생성 결과 영역 확장

- 사용자는 글자를 UI 안에 좁게 가두는 것이 아니라 `생성 결과` 영역을 넓혀 글자가 적절히 보이게 하길 원한다고 정정했다.
- 이전 5열 grid의 `minmax(0, 1fr)`는 한 줄 배치는 만들지만 각 배지의 텍스트 폭을 줄일 수 있어 의도와 맞지 않았다.
- 해결은 `main` 최대 폭을 넓히고, `생성 결과` 패널에 `output-panel` 클래스를 붙여 workspace 전체 폭을 쓰게 하는 것이다.
- 5개 배지 grid는 `repeat(5, max-content)`로 바꿔 텍스트가 필요한 실제 폭을 유지하게 했다.
- 검증은 focused 실패 테스트 확인 뒤 전체 unittest 82개 통과, HTML inline script 구문 검사 통과, `git diff --check` 통과, Playwright에서 `.output-panel`이 `main` 폭과 거의 같고 배지 `scrollWidth`가 `clientWidth` 이하임을 확인하는 방식으로 진행했다.

## 2026-05-24 생성 결과 오른쪽 배치 복구

- 사용자는 생성 결과가 동기화 오른쪽에 있어야 하는데 아래로 내려왔다고 지적했다.
- 원인은 `output-panel`에 `grid-column: 1 / -1`을 적용해 workspace 전체 폭을 차지하게 만든 것이다.
- 새 방향은 전체 폭 배치를 제거하고, workspace를 `동기화 좁은 열 + 생성 결과 넓은 열`로 조정하는 것이다.
- 좁은 화면에서는 기존처럼 1열로 내려가되, 데스크톱 폭에서는 생성 결과가 오른쪽에 남아야 한다.
- 구현은 `grid-column: 1 / -1`을 제거하고, workspace를 `minmax(300px, 0.32fr) minmax(780px, 1fr)`로 바꿔 오른쪽 생성 결과 열이 더 넓게 잡히도록 했다.
- 검증은 focused 실패 테스트 확인 뒤 전체 unittest 82개 통과, HTML inline script 구문 검사 통과, `git diff --check` 통과, Playwright에서 생성 결과 패널이 동기화 오른쪽에 있고 폭이 동기화보다 2배 이상임을 확인하는 방식으로 진행했다.

## 2026-05-24 UI 크기 조정 원복

- 사용자는 UI를 원래 스타일로 돌리되, 지금까지 바꾼 크기 조절만 되돌리라고 요청했다.
- 유지할 것은 결과 이력 배지의 `연금 1`, `로또 1` 라벨 표시다.
- 원복 대상은 `main` 폭 확장, workspace 열 비율 변경, `output-panel` 클래스, five-up 강제 grid, 배지 폭 강제 조정이다.
- 목표 상태는 기존 `main` 1120px, 기존 workspace 2열, flex-wrap 배지 리스트다.
- 구현 후 `output-panel` 클래스가 제거됐고, 생성 결과 패널은 다시 동기화 패널 오른쪽에 배치된다.
- 검증은 전체 unittest 82개 통과, HTML inline script 문법 검사 통과, `git diff --check` 통과, 브라우저에서 `outputClass: "panel"`과 `outputIsRightOfSync: true` 확인으로 진행했다.

## 2026-05-24 생성 결과 게임별 좌우 배치

- 사용자는 생성 결과의 구매내역이 로또 5개 다음 연금 5개로 한 줄 세로 목록이 되는 문제를 보고했다.
- 목표 배치는 로또 5개 세로 열과 연금 5개 세로 열을 좌우로 나누는 것이다.
- 당첨금액 영역도 같은 읽기 방식이 되도록 지난 당첨결과 이력 카드를 로또 열과 연금 열로 나누는 방향을 선택했다.
- 기존 출력 패널 폭은 직전 요청대로 원래 스타일을 유지해야 하므로, 패널 폭을 다시 넓히지 않고 내부 목록만 2열로 바꾼다.
- 모바일이나 좁은 폭에서는 1열로 내려가게 해서 텍스트가 잘리지 않도록 한다.
- 구현은 `ticket-summary split` 안에 `ticket-column` 2개를 만들고, 이력은 `history-list split` 안에 게임별 `history-column` 2개를 만드는 방식으로 진행했다.
- 검증은 새 focused 테스트 실패 확인 후 전체 unittest 84개 통과, HTML inline script 문법 검사 통과, `git diff --check` 통과, 브라우저에서 구매번호 열별 행 수 5개와 5개, 이력 열별 카드 수 1개와 1개 확인으로 진행했다.

## 2026-05-24 모바일 UI 개선

- 사용자는 모바일 실행 시 UI가 살짝 아쉽다고 보고했다.
- 390px 렌더링에서 상단 링크가 한 줄 전체 폭을 차지하고, 생성 결과 구매번호 목록이 10개 세로 행으로 길게 내려가는 점이 가장 눈에 띄었다.
- 데스크톱 배치와 기존 색상 체계는 유지하고, 모바일 전용 CSS만 조정하는 방향을 선택했다.
- 440px 이하에서는 상단 액션을 2열 그리드로 정리하고, 생성 결과 구매번호 목록은 로또 열과 연금 열을 유지하되 각 행을 카드형 1열로 압축한다.
- 통계 행, 패널 본문, 지난 당첨결과 카드와 배지는 모바일에서만 여백을 줄여 첫 화면 밀도를 개선한다.
- 구현 후 390px 폭에서 `top-actions`는 2열 그리드, 구매번호 목록은 `169px 169px` 2열, 로또와 연금 행 수는 각각 5개로 확인됐다.
- 검증은 focused 실패 테스트 확인 후 전체 unittest 86개 통과, HTML inline script 문법 검사 통과, `git diff --check` 통과, Browser 로컬 렌더 확인, 390px Playwright 렌더에서 `bodyScrollWidth: 390` 확인으로 진행했다.

## 2026-05-24 당첨확률 표시

- 사용자는 사이트에서 로또와 연금복권 당첨확률을 볼 수 있게 요청했다.
- 공식 값은 동행복권 기준으로 로또 6/45 1등 `1/8,145,060`, 전체 `1/42`이고, 연금복권720+ 1등 `1/5,000,000`, 전체 `1/10`이다.
- 로또 등위별 확률은 1등 `1/8,145,060`, 2등 `1/1,357,510`, 3등 `1/35,724`, 4등 `1/733`, 5등 `1/45`로 표시한다.
- 연금복권720+는 1등부터 7등과 보너스까지 공식 당첨구조 표의 확률을 표시한다.
- UI는 생성 결과 패널 안의 접힌 `당첨확률 보기` 섹션으로 추가해 기존 구매번호와 이력 흐름을 방해하지 않게 한다.

## 2026-05-24 P1 정리 및 연금복권 중복 등위 보완

- 사용자는 당첨확률 UI는 구현하지 않아도 된다고 결정했다.
- 따라서 당첨확률 UI를 요구하는 미구현 계약 테스트는 제거하고, 공식 확률 값 확인 기록만 남긴다.
- P3 GitHub token 저장은 집 컴퓨터 전용 사용이라는 운영 조건 때문에 이번 범위에서 변경하지 않는다.
- P2는 연금복권 한 장이 일반 등위와 보너스에 동시에 해당할 때 최상위 당첨만 표시해야 하는 문제다.
- 동행복권 안내의 중복 당첨 시 최상위 당첨금만 지급 규칙을 기준으로, 등위 계산 단계에서 최상위 1개만 반환하도록 보완한다.
- 구현 후 `check_pension`은 group과 number 값을 명시적으로 검증하고, 보너스가 낮은 suffix 등위와 겹치면 보너스만 반환한다.
- 검증은 `python -m unittest tests.test_pension`, `python -m unittest tests.test_pages`, `python -m unittest discover -s tests`, `python -m compileall dhlottery_checker`, `git diff --check`로 진행했다.

## 2026-05-24 누적 금액 표시

- 사용자는 당첨된 복권이 있으면 누적 당첨금액과 복권 금액을 숫자로 볼 수 있게 요청했다.
- 금액 표시는 기존 동기화 통계 행에 추가해 별도 패널을 늘리지 않는다.
- 누적 당첨금액은 `data/result-history.yml`의 `prizes` 금액과 개수를 합산한다.
- 복권금액은 지난 결과 이력의 `total_count`와 현재 `data/tickets.yml`에 남은 구매번호 수를 합산해 1장 1,000원으로 계산한다.
- 연금식 당첨금 문구는 총액 기준 숫자로 환산한다. 예를 들어 `월 100만원 x 10년`은 120,000,000원으로 계산한다.
- 현재 로컬 데이터 기준 렌더 검증 결과 누적 당첨금액은 5,000원, 누적 복권금액은 20,000원이다.
- 검증은 focused Pages 테스트, 전체 unittest 91개, HTML inline script Node 구문 검사, desktop과 390px Playwright 렌더, `git diff --check`로 진행했다.

## 2026-05-24 잔여 체크리스트 정리

- 2026-05-17 구간의 `변경사항을 커밋하고 원격에 푸시한다` 항목 4개는 실제 잔여 구현이 아니라 기록 누락으로 확인했다.
- 현재 `origin/main`은 해당 과거 작업들을 포함하고 있고, 로컬 `main`은 최근 두 기능 커밋만 앞서 있는 상태였다.

## 2026-05-24 유지보수 안정성 리뷰

- 기준선 검증은 `python -m unittest discover -s tests`, `python -m compileall dhlottery_checker`, `git diff --check`로 확인했다.
- 주요 리스크는 외부 HTTP 호출 자체보다 사용자 입력 YAML과 로컬 상태 파일 손상 시 CLI가 스택트레이스로 끝날 수 있는 점이다.
- `docs/ticket-entry.html`, `dhlottery_checker/runner.py`, `dhlottery_checker/ledger_scraper.py`는 크기가 커졌지만, 지금 당장 분리하면 기능 회귀 위험이 더 커서 이번 보수에서는 구조 분리를 하지 않는다.
- P2 보수 범위는 구매번호 설정 검증 메시지 정리, 검사 CLI의 입력 오류 종료 코드 정리, 중복 알림 상태 JSON 손상 복구, 상태 저장 원자성 보강으로 제한한다.
- 새 의존성은 추가하지 않는다.
- TDD 확인 결과 `tests.test_config`, `_run_check` focused 테스트, `tests.test_state`가 기존 구현에서 각각 실패했고, 보수 후 focused 테스트가 통과했다.
- 설정 오류는 `로또 numbers`, `연금복권 group`처럼 입력 필드를 알 수 있는 메시지로 정리한다.
- 상태 파일 JSON이 깨진 경우 중복 알림 상태만 빈 값으로 복구한다. 이 경우 같은 결과가 다시 알림될 수는 있지만, 검사 실행이 중단되는 것보다 안전하다.
- 전체 검증은 96개 unittest 통과, `python -m compileall dhlottery_checker` 통과, `git diff --check` 통과로 확인했다.

## 2026-05-24 누적 금액 색상 표시

- 사용자는 누적 당첨금액은 초록색, 누적 복권금액은 노란색 계열로 보이길 요청했다.
- 기존 통계 행 안에서 값 텍스트에만 색상을 입힌다. 새 카드나 레이아웃 변경은 하지 않는다.
- 당첨금액은 기존 `--good` 토큰을 재사용하고, 복권금액은 밝은 모드 `#9a6700`, 어두운 모드 `#f4c95d`를 사용한다.
- Playwright 렌더 확인 결과 밝은 모드는 당첨금액 `rgb(21, 122, 81)`, 복권금액 `rgb(154, 103, 0)`이고 어두운 모드는 당첨금액 `rgb(103, 215, 157)`, 복권금액 `rgb(244, 201, 93)`이다.

## 2026-05-31 최근 당첨결과와 예치금 경고 표시 보완

- 사용자는 새로고침해도 예치금 깜박임과 이번주 연금복권 미당첨 표시가 안 된다고 보고했다.
- 원인은 이전 수정이 feature 브랜치에만 있었고, 원격 `main`은 GitHub Actions 자동 커밋으로 앞서 있어서 Pages 배포 대상에 반영되지 않은 것이다.
- 원격 `main`의 구매번호는 이미 로또 1227회와 연금복권 318회로 갱신되어 있다. 따라서 “현재 구매번호 회차만 표시” 방식은 연금복권 317회 미당첨 결과도 숨기는 문제가 있다.
- 표시 기준을 `현재 구매번호 당첨결과`에서 `최근 당첨결과`로 바꾸고, `data/result-history.yml`에서 게임별 최신 완료 이력 1개씩만 보여주는 방식으로 수정한다.
- 이 방식이면 연금복권 317회 미당첨은 보이고, 더 오래된 316회 당첨은 기본 화면에서 빠져 이번주 당첨처럼 오해될 가능성이 줄어든다.
- 예치금 부족 상태는 `balance-low` 클래스에서 붉은색, 900 굵기, `balance-alert-blink` 0.8초 애니메이션으로 표시한다. `prefers-reduced-motion`에서는 애니메이션을 끈다.
- 연금복권 317회는 검사기로 확인한 결과 당첨 0개, 미당첨 5개이고 당첨번호는 3조 827917, 보너스 각조 719917이다.
- 브라우저 렌더 확인 결과 최근 당첨결과는 2건이고 로또 1226회, 연금복권 317회 미당첨 5개가 표시됐다.
- 같은 렌더에서 예치금 상태는 `stat-value balance-low`, `animation-name: balance-alert-blink`, `animation-duration: 0.8s`, `font-weight: 900`으로 확인됐다.

## 2026-05-31 예치금 경고 배경 깜박임 개선

- 사용자는 `충전 필요` 글씨 자체가 깜박이는 것이 디자인적으로 좋아 보이지 않는다고 했다.
- 새 방향은 글자를 고정된 붉은 굵은 텍스트로 두고, 글자 뒤 배경만 옅은 경고 배지처럼 깜박이게 하는 것이다.
- 기존 통계 행 높이와 우측 정렬은 유지한다. 새 패널이나 큰 레이아웃 변경은 하지 않는다.
- 구현은 `--bad-alert-bg`, `--bad-alert-bg-strong` 토큰을 추가하고, `balance-alert-background` keyframes가 `background-color`만 바꾸는 방식이다.
- 브라우저 렌더 확인 결과 `충전 필요`는 `opacity: 1`, `animation-name: balance-alert-background`, `animation-duration: 0.8s`, `padding: 2px 8px`, `border-radius: 8px`로 표시됐다.

## 2026-05-31 최근 당첨결과 고정과 과거 기록 접힘

- 사용자 요청은 최근 당첨결과를 생성 결과 첫 번째에 고정하고, 과거 기록 3회분을 접었다 펼 수 있게 보여주는 것이다.
- 최근 당첨결과는 기존 `latestResultHistoryEntries` 기준을 유지한다. 게임별 최신 완료 결과가 보이면 로또와 연금복권이 동시에 확인된다.
- 과거 기록은 최신 고정 항목과 중복되면 혼란이 생기므로 최신 항목을 제외한 다음 3건만 표시한다.
- 미당첨 표기는 `historySummary`와 `appendHistoryTicketBadge`가 이미 처리하므로 새 표시 체계를 만들지 않고 기존 카드 렌더링을 재사용한다.
- 브라우저 검증 결과 생성 결과 첫 자식은 `history-block`이고, 최근 당첨결과는 2건 표시되며 과거 당첨기록은 기본 닫힘 상태에서 클릭 후 열렸다.
- 같은 검증에서 과거 기록 안에 `미당첨` 문구가 유지되는 것을 확인했다.
- 검증은 focused Pages 테스트 3개, `tests.test_pages` 22개, 전체 unittest 100개, `python -m compileall dhlottery_checker`, HTML inline script 문법 검사, `git diff --check`, 브라우저 렌더로 진행했다.

## 2026-05-31 예치금 경고 부드러운 배경 펄스

- 사용자 피드백은 `충전 필요` 배경 깜박임이 너무 끊겨 보여 성능저하처럼 느껴진다는 것이다.
- 원인은 `animation: balance-alert-background 0.8s steps(2, start) infinite`가 배경색을 즉시 전환하기 때문이다.
- 방향은 글자 색과 굵기, 배지 크기는 유지하고, 배경 강조만 `::before` 가상 요소의 opacity 펄스로 부드럽게 처리하는 것이다.
- opacity 애니메이션은 작은 배지에서 부드럽고 브라우저가 처리하기 쉬워 현재 요구에 맞다.
- 구현 후 브라우저에서 `충전 필요` 텍스트는 `opacity: 1`, `font-weight: 900`이고, `::before`가 `balance-alert-background 1.6s ease-in-out infinite`로 움직이는 것을 확인했다.
- 검증은 focused Pages 테스트, HTML inline script 문법 검사, 전체 unittest 100개, `python -m compileall dhlottery_checker`, `git diff --check`, 브라우저 렌더로 진행했다.
