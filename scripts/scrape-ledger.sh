#!/usr/bin/env bash
# 리눅스에서 동행복권 구매내역을 가져오는 스크립트
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

python_bin="${PYTHON_BIN:-python3}"
ticket_path="${TICKET_PATH:-data/tickets.yml}"
account_path="${ACCOUNT_PATH:-data/account.yml}"
profile_dir="${PROFILE_DIR:-.browser/dhlottery}"
env_file="${ENV_FILE:-.env}"
login_url="${LOGIN_URL:-https://www.dhlottery.co.kr/login}"
main_url="${MAIN_URL:-https://www.dhlottery.co.kr/main}"
max_tickets="${MAX_TICKETS:-30}"
headless="${HEADLESS:-1}"
show_progress="${SHOW_PROGRESS:-1}"
append="${APPEND:-0}"

args=(
  "-m" "dhlottery_checker" "scrape-ledger"
  "--tickets" "$ticket_path"
  "--account" "$account_path"
  "--profile-dir" "$profile_dir"
  "--env-file" "$env_file"
  "--login-url" "$login_url"
  "--main-url" "$main_url"
  "--max-tickets" "$max_tickets"
)

if [[ "$append" == "1" || "$append" == "true" ]]; then
  args+=("--append")
fi

if [[ "$headless" != "0" && "$headless" != "false" ]]; then
  args+=("--headless")
fi

if [[ "$show_progress" != "0" && "$show_progress" != "false" ]]; then
  args+=("--verbose")
fi

"$python_bin" "${args[@]}"
