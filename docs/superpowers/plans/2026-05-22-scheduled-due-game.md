# Scheduled Due Game Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 예약 실행에서 도래한 복권 종류만 검사하도록 GitHub Actions 인자 전달을 보완한다.

**Architecture:** `schedule-due`는 이미 `due_games`를 GitHub output으로 내보낸다. `check-results.yml`은 예약 이벤트일 때 그 값을 읽어 `python -m dhlottery_checker check`에 `--game lotto`, `--game pension`, 또는 `--game all`을 명시한다.

**Tech Stack:** GitHub Actions Bash, Python unittest.

---

### Task 1: Workflow Contract

**Files:**
- Create: `tests/test_workflows.py`
- Modify: `.github/workflows/check-results.yml`

- [x] **Step 1: Write the failing workflow contract test**

Add a test that reads `.github/workflows/check-results.yml` and asserts the check step consumes `steps.notification_schedule.outputs.due_games`, computes `game_arg`, and passes `--game "$game_arg"`.

- [x] **Step 2: Verify the test fails**

Run `python -m unittest tests.test_workflows.WorkflowContractTest.test_check_results_uses_due_games_for_scheduled_runs`.

- [x] **Step 3: Implement the workflow shell change**

Add `DUE_GAMES` to the check step env, compute `game_arg` for scheduled runs, and include `--game "$game_arg"` in the check command.

- [x] **Step 4: Verify focused and full tests**

Run the focused workflow test, then `python -m unittest discover -s tests`, then `git diff --check`.

- [x] **Step 5: Commit**

Commit the workflow and test change as one logical unit.
