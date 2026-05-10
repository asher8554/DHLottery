#!/usr/bin/env bash
# 시놀로지 작업 스케줄러에서 Docker로 스크래퍼를 실행하는 스크립트
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
image="${DHLOTTERY_IMAGE:-dhlottery-synology:latest}"
ssh_dir="${DHLOTTERY_SSH_DIR:-$repo_root/.ssh}"
container_name="${DHLOTTERY_CONTAINER_NAME:-dhlottery-scraper}"

mkdir -p "$repo_root/logs" "$repo_root/.state" "$ssh_dir"

docker_env=("-e" "TZ=Asia/Seoul")
for name in \
  PYTHON_BIN \
  TICKET_PATH \
  ACCOUNT_PATH \
  PROFILE_DIR \
  ENV_FILE \
  LOGIN_URL \
  MAIN_URL \
  MAX_TICKETS \
  HEADLESS \
  SHOW_PROGRESS \
  APPEND \
  COMMIT_MESSAGE \
  NO_PUSH \
  LOCK_DIR
do
  if [[ -n "${!name:-}" ]]; then
    docker_env+=("-e" "$name=${!name}")
  fi
done

docker run --rm \
  --name "$container_name" \
  "${docker_env[@]}" \
  -v "$repo_root:/app" \
  -v "$ssh_dir:/root/.ssh" \
  -w /app \
  "$image" \
  bash scripts/scrape-ledger-and-push.sh
