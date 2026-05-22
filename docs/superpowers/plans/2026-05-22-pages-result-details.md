# Pages Result Details Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Pages에서 최근 당첨번호와 구매번호별 결과 요약을 함께 확인할 수 있게 한다.

**Architecture:** 검사 실행기가 `data/result-history.yml`에 회차별 공개 당첨번호와 비민감 티켓 결과를 저장한다. 정적 Pages는 기존 raw YAML 로드 흐름을 유지하고, 새 필드를 읽어 결과 카드를 렌더링한다.

**Tech Stack:** Python unittest, PyYAML, HTML/CSS/vanilla JavaScript, GitHub Pages.

---

### Task 1: Result History Data

**Files:**
- Modify: `tests/test_runner.py`
- Modify: `dhlottery_checker/runner.py`

- [x] **Step 1: Write the failing test**

Add a test that creates lotto and pension `Outcome` values with winning result fields, calls `write_result_history`, and asserts the YAML contains `winning` and `tickets` details without storing selected ticket numbers.

- [x] **Step 2: Run the focused test**

Run `python -m unittest tests.test_runner.RunnerTest.test_write_result_history_includes_page_result_details`.

Expected result is failure because `Outcome` does not yet expose the result detail fields.

- [x] **Step 3: Add minimal implementation**

Extend `Outcome` with optional winning detail fields, populate them in `_lotto_outcomes` and `_pension_outcomes`, and include those fields in `_result_history_entries`.

- [x] **Step 4: Run focused tests**

Run `python -m unittest tests.test_runner.RunnerTest.test_write_result_history_includes_page_result_details tests.test_runner.RunnerTest.test_write_result_history_summarizes_resolved_groups_without_numbers`.

Expected result is pass.

### Task 2: Pages Result Cards

**Files:**
- Modify: `docs/ticket-entry.html`

- [x] **Step 1: Improve history parsing**

Teach `parseResultHistoryYaml` to read the new `winning` and `tickets` nested fields from `data/result-history.yml`.

- [x] **Step 2: Render result details**

Replace plain history rows with cards that show summary, public winning numbers, and ticket result badges.

- [x] **Step 3: Verify HTML script syntax**

Run a Node syntax check against the inline script extracted from `docs/ticket-entry.html`.

Expected result is no syntax error.

### Task 3: Project Verification

**Files:**
- Modify: `checklist.md`
- Modify: `context-notes.md`

- [x] **Step 1: Run full tests**

Run `python -m unittest discover -s tests`.

Expected result is all tests pass.

- [x] **Step 2: Run whitespace check**

Run `git diff --check`.

Expected result is no output.

- [x] **Step 3: Commit**

Commit one logical change with a Korean commit message after verification passes.
