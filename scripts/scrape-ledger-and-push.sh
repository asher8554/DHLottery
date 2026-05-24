#!/usr/bin/env bash
# 리눅스에서 구매내역과 예치금을 가져와 커밋하고 원격에 올리는 스크립트
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

ticket_path="${TICKET_PATH:-data/tickets.yml}"
account_path="${ACCOUNT_PATH:-data/account.yml}"
status_path="${SCRAPER_STATUS_PATH:-data/scraper-status.yml}"
scraper_source="${SCRAPER_SOURCE:-linux}"
commit_message="${COMMIT_MESSAGE:-구매번호 자동 반영}"
no_push="${NO_PUSH:-0}"
lock_dir="${LOCK_DIR:-.state/scrape-ledger.lock}"
lock_stale_minutes="${LOCK_STALE_MINUTES:-60}"
target_branch="${TARGET_BRANCH:-main}"

mkdir -p "$(dirname "$lock_dir")"
if ! mkdir "$lock_dir" 2>/dev/null; then
  if find "$lock_dir" -maxdepth 0 -mmin +"$lock_stale_minutes" 2>/dev/null | grep -q .; then
    echo "오래된 스크래퍼 lock을 정리합니다. $lock_dir"
    rmdir "$lock_dir" 2>/dev/null || {
      echo "스크래퍼 lock을 정리하지 못했습니다. $lock_dir"
      exit 0
    }
    mkdir "$lock_dir"
  else
    echo "이미 스크래퍼가 실행 중입니다."
    exit 0
  fi
fi
trap 'rmdir "$lock_dir"' EXIT

git config --global --add safe.directory "$repo_root" >/dev/null 2>&1 || true
git config user.name "${GIT_AUTHOR_NAME:-synology-dhlottery}"
git config user.email "${GIT_AUTHOR_EMAIL:-synology-dhlottery@example.local}"

if [[ -z "${GIT_SSH_COMMAND:-}" && -f /root/.ssh/id_ed25519 ]]; then
  export GIT_SSH_COMMAND="ssh -i /root/.ssh/id_ed25519 -o IdentitiesOnly=yes"
fi

ensure_no_rebase_in_progress() {
  local rebase_merge rebase_apply
  rebase_merge="$(git rev-parse --git-path rebase-merge)"
  rebase_apply="$(git rev-parse --git-path rebase-apply)"

  if [[ -d "$rebase_merge" || -d "$rebase_apply" ]]; then
    echo "이전 rebase 상태가 남아 있습니다. git rebase --abort 후 다시 실행하세요."
    exit 1
  fi
}

ensure_target_branch() {
  local current_branch
  current_branch="$(git branch --show-current || true)"
  if [[ "$current_branch" == "$target_branch" ]]; then
    return
  fi

  if [[ -z "$current_branch" ]]; then
    echo "detached HEAD 상태입니다. $target_branch 브랜치로 전환합니다."
  else
    echo "현재 브랜치가 $current_branch 입니다. $target_branch 브랜치로 전환합니다."
  fi

  git fetch origin "$target_branch"
  if git show-ref --verify --quiet "refs/heads/$target_branch"; then
    git checkout "$target_branch"
  else
    git checkout -b "$target_branch" "origin/$target_branch"
  fi
}

ensure_git_ready() {
  ensure_no_rebase_in_progress
  ensure_target_branch
  git pull --rebase origin "$target_branch"
}

yaml_quote() {
  local value="${1//\"/\\\"}"
  printf '"%s"' "$value"
}

scraper_source_label() {
  case "$1" in
    synology)
      printf "시놀로지 실행"
      ;;
    windows)
      printf "Windows 실행"
      ;;
    linux)
      printf "Linux 실행"
      ;;
    *)
      printf "%s" "$1"
      ;;
  esac
}

write_scraper_status() {
  local updated_at source_label
  updated_at="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  source_label="$(scraper_source_label "$scraper_source")"

  mkdir -p "$(dirname "$status_path")"
  {
    printf "source: "
    yaml_quote "$scraper_source"
    printf "\nsource_label: "
    yaml_quote "$source_label"
    printf "\nupdated_at: "
    yaml_quote "$updated_at"
    printf "\n"
  } > "$status_path"
}

ensure_git_ready

bash "$repo_root/scripts/scrape-ledger.sh"
python -m dhlottery_checker prune-sent-tickets --tickets "$ticket_path" --status-json .state/check-status.json --history data/result-history.yml
write_scraper_status

change_paths=("$ticket_path")
if [[ -n "$account_path" ]]; then
  change_paths+=("$account_path")
fi
if [[ -n "$status_path" ]]; then
  change_paths+=("$status_path")
fi

git add -- "${change_paths[@]}"

if git diff --cached --quiet -- "${change_paths[@]}"; then
  echo "구매번호와 예치금 변경사항이 없습니다."
  exit 0
fi

git commit -m "$commit_message"

if [[ "$no_push" == "1" || "$no_push" == "true" ]]; then
  echo "커밋까지만 완료했습니다. NO_PUSH=1 설정으로 원격 푸시는 건너뜁니다."
  exit 0
fi

git pull --rebase origin "$target_branch"
git push origin "$target_branch"

echo "GitHub Pages에서 새 구매번호와 예치금을 확인할 수 있습니다."
