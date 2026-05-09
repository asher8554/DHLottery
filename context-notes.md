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
