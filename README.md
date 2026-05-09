# DHLottery

동행복권에서 직접 구매한 로또 6/45와 연금복권720+ 번호를 당첨번호와 비교하고, 결과를 카카오톡 나에게 보내기로 알리는 도구입니다.

## 중요한 제한

이 저장소는 동행복권 로그인, 복권 자동 구매, 예치금 충전, 은행이체를 구현하지 않습니다.
공식 구매 API가 확인되지 않았고, 계정 및 금융정보 자동화는 보안과 약관 리스크가 큽니다.

## 보안 원칙

- 실제 구매번호는 `tickets.yml` 또는 GitHub Actions Secret `TICKETS_YAML`에만 둡니다.
- `tickets.yml`은 `.gitignore`에 포함되어 커밋되지 않습니다.
- 카카오 토큰은 GitHub Actions Secrets에만 저장합니다.
- 저장소는 private로 운영하는 것을 전제로 합니다.

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

## GitHub Actions 실행

워크플로는 `.github/workflows/check-results.yml`에 있습니다.
기본 스케줄은 한국시간 기준 연금복권 목요일 19시 15분, 로또 토요일 21시 10분입니다.
GitHub cron은 UTC 기준이라 파일에는 각각 `15 10 * * 4`, `10 12 * * 6`으로 적혀 있습니다.

발표 반영이 늦어지는 날을 고려해 즉시 확인하지 않도록 잡았습니다.
원하면 워크플로 파일의 cron만 바꾸면 됩니다.

## 설정 문서

- GitHub 저장소와 Secret 설정은 [docs/github-setup.md](docs/github-setup.md)를 보세요.
- 카카오톡 나에게 보내기 설정은 [docs/kakao-setup.md](docs/kakao-setup.md)를 보세요.

## 테스트

```powershell
python -m unittest discover -s tests
```

