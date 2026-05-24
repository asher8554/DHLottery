# Maintenance Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 구매번호 설정 오류와 중복 알림 상태 파일 손상 상황에서도 실행기가 이해 가능한 오류를 내고 안정적으로 계속 동작하게 한다.

**Architecture:** 큰 구조 변경 없이 CLI 진입점과 상태 저장 모듈의 경계만 보강한다. `config.py`는 사용자 입력 검증 메시지를 담당하고, `runner.py`는 CLI 실패를 2번 종료 코드로 정리하며, `state.py`는 알림 중복 방지 상태를 원자적으로 저장한다.

**Tech Stack:** Python 표준 라이브러리, PyYAML, unittest.

---

### Task 1: 구매번호 설정 오류 처리

**Files:**
- Modify: `tests/test_config.py`
- Modify: `tests/test_runner.py`
- Modify: `dhlottery_checker/config.py`
- Modify: `dhlottery_checker/runner.py`

- [x] **Step 1: Write failing config validation tests**

```python
def test_rejects_non_numeric_lotto_number_with_clear_error(self):
    os.environ["TICKETS_YAML"] = """
lotto:
  tickets:
    - round: 1222
      numbers: [1, 2, bad, 4, 5, 6]
"""
    with self.assertRaisesRegex(ValueError, "로또 numbers"):
        load_ticket_config()

def test_rejects_non_numeric_pension_group_with_clear_error(self):
    os.environ["TICKETS_YAML"] = """
pension:
  tickets:
    - round: 314
      group: bad
      number: "060727"
"""
    with self.assertRaisesRegex(ValueError, "연금복권 group"):
        load_ticket_config()
```

- [x] **Step 2: Run config tests to verify failure**

Run: `python -m unittest tests.test_config`.
Expected: Fail because raw conversion errors leak instead of the intended clear `ValueError`.

- [x] **Step 3: Write failing CLI error handling test**

```python
def test_check_returns_input_error_for_invalid_ticket_config(self):
    with patch("dhlottery_checker.runner.load_ticket_config", side_effect=ValueError("bad ticket")):
        with patch("builtins.print") as print_mock:
            result = _run_check(self._args(force_notify=False))

    self.assertEqual(result, 2)
    self.assertIn("구매번호 설정 오류", print_mock.call_args.args[0])
```

- [x] **Step 4: Run runner test to verify failure**

Run: `python -m unittest tests.test_runner.RunnerTest.test_check_returns_input_error_for_invalid_ticket_config`.
Expected: Fail because `_run_check` currently lets the exception escape.

- [x] **Step 5: Implement minimal validation and CLI handling**

In `config.py`, wrap number and group conversions so they raise the existing Korean validation messages.

In `runner.py`, catch `ValueError` from `load_ticket_config`, print a concise stderr message, and return `2`.

- [x] **Step 6: Verify Task 1**

Run: `python -m unittest tests.test_config tests.test_runner`.
Expected: All tests pass.

### Task 2: 중복 알림 상태 파일 내구성

**Files:**
- Modify: `tests/test_state.py`
- Modify: `dhlottery_checker/state.py`

- [x] **Step 1: Write failing corrupted-state recovery test**

```python
def test_load_ignores_corrupt_json_state(self):
    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "sent-results.json"
        path.write_text("{bad", encoding="utf-8")

        state = SentState.load(path)

    self.assertEqual(state.sent, {})
```

- [x] **Step 2: Write failing atomic save contract test**

```python
def test_save_writes_valid_state_json(self):
    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "sent-results.json"
        state = SentState(path, {})
        state.mark_sent("abc", "lotto", 1222)

        state.save()

        self.assertIn("abc", json.loads(path.read_text(encoding="utf-8"))["sent"])
        self.assertFalse(path.with_suffix(".json.tmp").exists())
```

- [x] **Step 3: Run state tests to verify failure**

Run: `python -m unittest tests.test_state`.
Expected: Fail on corrupt JSON recovery before implementation.

- [x] **Step 4: Implement minimal state hardening**

In `SentState.load`, catch `json.JSONDecodeError` and return an empty state.

In `SentState.save`, write to a sibling temporary file and replace the target with `Path.replace`.

- [x] **Step 5: Verify Task 2**

Run: `python -m unittest tests.test_state`.
Expected: All tests pass.

### Task 3: Final verification and commit

**Files:**
- Modify: `checklist.md`
- Modify: `context-notes.md`
- Modify: `docs/superpowers/plans/2026-05-24-maintenance-hardening.md`

- [x] **Step 1: Run full verification**

Run: `python -m unittest discover -s tests`.
Expected: All tests pass.

Run: `python -m compileall dhlottery_checker`.
Expected: Exit code 0.

Run: `git diff --check`.
Expected: Exit code 0.

- [x] **Step 2: Commit**

```bash
git add dhlottery_checker/config.py dhlottery_checker/runner.py dhlottery_checker/state.py tests/test_config.py tests/test_runner.py tests/test_state.py checklist.md context-notes.md docs/superpowers/plans/2026-05-24-maintenance-hardening.md
git commit -m "실행 안정성 보강"
```
