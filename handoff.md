# 다음 작업 인수인계

## 현재 상태

- 동행복권 자동 구매, 자동 로그인, 예치금 충전, 은행이체 자동화는 구현하지 않는다.
- 사용자가 직접 구매한 번호를 기록하고, 발표 후 당첨번호와 비교해 카카오톡으로 결과를 받는 구조로 구현했다.
- 로또 6/45와 연금복권720+ 결과 조회 및 등수 계산이 구현되어 있다.
- 카카오톡 나에게 보내기 알림이 로컬과 GitHub Actions에서 모두 성공했다.
- GitHub Actions 수동 실행도 성공했다.
- 실제 구매번호는 저장소에 커밋하지 않고 `TICKETS_YAML` GitHub Secret으로만 전달한다.
- 로컬의 `data/tickets.yml`은 `.gitignore`에 포함되어 커밋되지 않는다.

## 핵심 파일

- `dhlottery_checker/runner.py`: 전체 확인 흐름.
- `dhlottery_checker/lotto.py`: 로또 당첨번호 조회와 등수 계산.
- `dhlottery_checker/pension.py`: 연금복권 당첨번호 조회와 등수 계산.
- `dhlottery_checker/kakao.py`: 카카오톡 알림 전송.
- `dhlottery_checker/config.py`: 구매번호 YAML 로딩.
- `.github/workflows/check-results.yml`: GitHub Actions 스케줄 실행.
- `scripts/sync-tickets-secret.ps1`: 로컬 `data/tickets.yml`을 `TICKETS_YAML` Secret으로 업로드.
- `docs/github-setup.md`: GitHub Secret 및 Actions 설정 문서.
- `docs/kakao-setup.md`: 카카오톡 알림 설정 문서.

## 운영 루틴

1. 사용자가 동행복권에서 직접 복권을 구매한다.
2. 구매한 번호를 로컬 `data/tickets.yml`에 적는다.
3. 저장소 루트에서 아래 명령을 실행한다.

```powershell
.\scripts\sync-tickets-secret.ps1
```

4. GitHub Actions 수동 실행 또는 예약 실행을 기다린다.
5. 발표 후 카카오톡으로 당첨 여부와 당첨금 정보를 받는다.

## 현재 GitHub Secrets

아래 Secret이 필요하다.

- `TICKETS_YAML`: 실제 구매번호 YAML.
- `KAKAO_REST_API_KEY`: 카카오 REST API 키.
- `KAKAO_REFRESH_TOKEN`: 카카오 refresh token.
- `STATE_HASH_SALT`: 중복 알림 상태 파일에 구매번호 원문을 남기지 않기 위한 임의 문자열.
- `KAKAO_CLIENT_SECRET`: 카카오 Client Secret이 ON인 경우에만 필요하다.

## 스케줄

현재 기본 스케줄은 한국시간 기준이다.

- 연금복권720+: 목요일 19시 15분.
- 로또 6/45: 토요일 21시 10분.

워크플로 파일의 cron은 UTC 기준이므로 수정할 때 한국시간에서 9시간을 빼야 한다.

## 검증 명령

```powershell
python -m unittest discover -s tests
python -m dhlottery_checker check --tickets data\tickets.example.yml --dry-run --no-state
.\scripts\sync-tickets-secret.ps1 -DryRun
```

실제 카카오톡 알림 테스트는 비밀값을 설정한 상태에서 실행한다.

```powershell
python -m dhlottery_checker check --tickets data\tickets.yml --notify --no-state
```

## 다음에 만들 만한 기능

아직 사용자가 실제 복권 구매 인터페이스를 경험하지 않았기 때문에 입력 도구는 보류했다.
다음에 이어서 작업한다면 아래 중 하나부터 검토한다.

### 1. 구매번호 입력 도구

목표는 `data/tickets.yml`을 직접 편집하지 않게 하는 것이다.

예상 명령은 아래와 같다.

```powershell
.\scripts\add-ticket.ps1
```

질문 형태로 입력받을 수 있다.

- 게임 종류: lotto 또는 pension.
- 회차.
- 라벨.
- 로또 번호 6개 또는 연금복권 조/6자리 번호.
- 입력 후 `data/tickets.yml` 저장.
- 선택적으로 `sync-tickets-secret.ps1` 실행.

### 2. 다음 회차 복사 도구

같은 번호를 계속 살 경우, 기존 번호를 다음 회차로 복사하는 명령을 만들 수 있다.

```powershell
.\scripts\copy-next-round.ps1
```

로또와 연금복권의 회차 증가 규칙을 단순히 `+1`로 처리할지, 동행복권 최신 회차 조회 결과를 기준으로 할지 결정해야 한다.

### 3. 구매 리마인더

구매 자동화는 하지 않지만, 구매 시점에 카카오톡으로 알림을 보내는 기능은 가능하다.
예를 들어 로또는 토요일 구매 마감 전, 연금복권은 원하는 요일에 리마인더를 보낼 수 있다.

## 하지 않기로 한 것

아래 기능은 구현하지 않는다.

- 동행복권 자동 로그인.
- 복권 자동 구매.
- 번호 선택과 구매 버튼 자동 클릭.
- 예치금 충전 자동화.
- 은행이체 자동화.
- 로그인된 브라우저 세션을 조작하는 마우스 매크로.

이유는 보안, 약관, 금전성 거래 오작동 리스크가 크기 때문이다.

## 주의사항

- 실제 토큰, REST API 키, refresh token, 구매번호는 채팅이나 커밋에 남기지 않는다.
- `data/tickets.yml`은 커밋하지 않는다.
- 카카오 refresh token이 노출되면 새로 발급하고 GitHub Secret을 교체한다.
- GitHub Actions에서 실패하면 먼저 `Validate required secrets` 단계의 오류를 확인한다.
