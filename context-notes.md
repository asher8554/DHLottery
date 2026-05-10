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
