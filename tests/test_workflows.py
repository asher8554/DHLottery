# GitHub Actions 워크플로의 주요 실행 계약을 검증하는 테스트
from pathlib import Path
import unittest


class WorkflowContractTest(unittest.TestCase):
    def test_check_results_uses_due_games_for_scheduled_runs(self):
        workflow = Path(".github/workflows/check-results.yml").read_text(encoding="utf-8")

        self.assertIn("DUE_GAMES: ${{ steps.notification_schedule.outputs.due_games || 'all' }}", workflow)
        self.assertIn('game_arg="all"', workflow)
        self.assertIn('if [ "$GITHUB_EVENT_NAME" = "schedule" ]; then', workflow)
        self.assertIn('case "$DUE_GAMES" in', workflow)
        self.assertIn('lotto) game_arg="lotto" ;;', workflow)
        self.assertIn('pension) game_arg="pension" ;;', workflow)
        self.assertIn('--game "$game_arg"', workflow)

    def test_check_results_prunes_result_history_rounds(self):
        workflow = Path(".github/workflows/check-results.yml").read_text(encoding="utf-8")

        self.assertIn(
            "prune-sent-tickets --tickets data/tickets.yml --status-json .state/check-status.json --history data/result-history.yml",
            workflow,
        )

    def test_check_results_commits_history_after_notification_failure(self):
        workflow = Path(".github/workflows/check-results.yml").read_text(encoding="utf-8")

        self.assertIn("id: check-results", workflow)
        self.assertIn("if: ${{ always() && steps.ticket-file.outputs.has_tickets == 'true' && steps.notification_schedule.outputs.should_run == 'true' }}", workflow)
        self.assertIn('if [ "${{ steps.check-results.outcome }}" = "success" ]; then', workflow)
        self.assertIn("git add data/result-history.yml", workflow)


if __name__ == "__main__":
    unittest.main()
