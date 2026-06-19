import unittest
import asyncio
import json
import os
import shutil
from unittest.mock import AsyncMock, patch
from click.testing import CliRunner
from personaforge.backend.app.cli.main import cli


class TestCLIE2E(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()
        self.test_dir = "test_workspace"
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        os.makedirs(self.test_dir)
        os.chdir(self.test_dir)

    def tearDown(self):
        os.chdir("..")
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_init_command(self):
        result = self.runner.invoke(cli, ["init"])
        self.assertEqual(result.exit_code, 0)
        self.assertTrue(os.path.exists("personaforge.yaml"))
        self.assertTrue(os.path.exists("personas/angry_customer.yaml"))
        self.assertTrue(os.path.exists("scenarios/telecom_refund.yaml"))
        self.assertTrue(os.path.exists("policies/refund.md"))

    @patch("personaforge.backend.app.cli.main.ElevenLabsProvider")
    @patch("personaforge.backend.app.personas.engine.LLMClient")
    @patch("personaforge.backend.app.judge.evaluator.LLMClient")
    def test_run_command_mocked(self, mock_judge_llm, mock_engine_llm, mock_provider):
        # Setup init
        self.runner.invoke(cli, ["init"])

        # Mock ElevenLabsProvider
        instance = mock_provider.return_value
        instance.connect = AsyncMock()
        instance.disconnect = AsyncMock()
        instance.send_text = AsyncMock()
        instance.send_audio = AsyncMock()

        # Mock receive_events to return one agent response and then end
        async def mock_events():
            yield {
                "type": "agent_response",
                "agent_response": {"content": "Hello, how can I help you today?"},
            }
            # Give it a bit of time to process
            await asyncio.sleep(0.1)

        instance.receive_events.return_value = mock_events()

        # Mock LLMClient for engine
        engine_llm_instance = mock_engine_llm.return_value
        engine_llm_instance.get_completion = AsyncMock(
            return_value="I'd like a refund."
        )

        # Mock determine_action to return END_CALL after first turn to avoid infinite loop
        from personaforge.backend.app.personas.engine import (
            BehaviorAction,
            BehaviorActionType,
        )

        first_call = True

        async def mock_get_structured_completion(*args, **kwargs):
            nonlocal first_call
            if first_call:
                first_call = False
                return BehaviorAction(
                    action=BehaviorActionType.SPEAK, reason="Initial request"
                )
            return BehaviorAction(action=BehaviorActionType.END_CALL, reason="Finished")

        engine_llm_instance.get_structured_completion = AsyncMock(
            side_effect=mock_get_structured_completion
        )

        # Mock JudgeEngine LLM
        judge_llm_instance = mock_judge_llm.return_value
        judge_llm_instance.get_completion = AsyncMock(
            return_value="Summary of conversation"
        )

        # Mock judge structured completion for failures
        from personaforge.backend.app.judge.evaluator import LLMFailures

        judge_llm_instance.get_structured_completion = AsyncMock(
            return_value=LLMFailures(failures=[])
        )

        # Update personaforge.yaml with a dummy agent_id
        with open("personaforge.yaml", "r") as f:
            import yaml

            config = yaml.safe_load(f)
        config["agent"]["agent_id"] = "test-agent-id"
        with open("personaforge.yaml", "w") as f:
            yaml.dump(config, f)

        # Also remove agent_id from scenario to ensure it uses config
        with open("scenarios/telecom_refund.yaml", "r") as f:
            scenario = yaml.safe_load(f)
        if "agent_id" in scenario:
            del scenario["agent_id"]
        with open("scenarios/telecom_refund.yaml", "w") as f:
            yaml.dump(scenario, f)

        # Use --dry-run to avoid DB issues
        result = self.runner.invoke(
            cli, ["run", "scenarios/telecom_refund.yaml", "--count", "1", "--dry-run"]
        )

        self.assertEqual(result.exit_code, 0)
        self.assertIn("Run completed", result.output)
        self.assertTrue(os.path.exists("reports/latest.json"))

    def test_report_command(self):
        # Create a dummy report with new structure
        os.makedirs("reports", exist_ok=True)
        report_data = {
            "report_id": "test-report",
            "timestamp": "2026-06-18T12:00:00",
            "total_cost": 0.50,
            "results": [
                {
                    "conversation_id": "test-id",
                    "persona": "angry_customer",
                    "history": [],
                    "evaluation": {
                        "pass_status": True,
                        "failures": [],
                        "summary": "Great",
                    },
                },
                {
                    "conversation_id": "test-id-2",
                    "persona": "angry_customer",
                    "history": [],
                    "evaluation": {
                        "pass_status": False,
                        "failures": [
                            {
                                "category": "hallucination",
                                "severity": "high",
                                "reason": "Lied about price",
                            }
                        ],
                        "summary": "Bad",
                    },
                },
            ],
        }
        with open("reports/latest.json", "w") as f:
            json.dump(report_data, f)

        result = self.runner.invoke(cli, ["report"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Total Conversations: 2", result.output)
        self.assertIn("Pass Rate:           50.0%", result.output)
        self.assertIn("hallucination", result.output)
        self.assertIn("Total Cost:          $0.50", result.output)

    @patch("personaforge.backend.app.cli.main.asyncio.run")
    def test_ci_command_pass(self, mock_asyncio_run):
        self.runner.invoke(cli, ["init"])
        # Create a passing report data
        results = [
            {
                "conversation_id": "test-id",
                "persona": "angry_customer",
                "history": [],
                "evaluation": {"pass_status": True, "failures": [], "summary": "Great"},
            }
        ]
        mock_asyncio_run.return_value = results

        # Set dry run env var to avoid DB in CI
        os.environ["PERSONAFORGE_CI_DRY_RUN"] = "true"
        result = self.runner.invoke(
            cli, ["ci", "--scenario", "scenarios/telecom_refund.yaml"]
        )
        # Since we use sys.exit(0), CliRunner captures it as exit_code 0
        self.assertEqual(result.exit_code, 0)
        self.assertIn("✅ CI PASSED", result.output)

    @patch("personaforge.backend.app.cli.main.asyncio.run")
    def test_ci_command_fail(self, mock_asyncio_run):
        self.runner.invoke(cli, ["init"])
        # Create a failing report data (hallucination)
        results = [
            {
                "conversation_id": "test-id",
                "persona": "angry_customer",
                "history": [],
                "evaluation": {
                    "pass_status": False,
                    "failures": [
                        {
                            "category": "hallucination",
                            "severity": "high",
                            "reason": "Lied about price",
                        }
                    ],
                    "summary": "Bad",
                },
            }
        ]
        mock_asyncio_run.return_value = results

        os.environ["PERSONAFORGE_CI_DRY_RUN"] = "true"
        result = self.runner.invoke(
            cli, ["ci", "--scenario", "scenarios/telecom_refund.yaml"]
        )
        # sys.exit(1) is captured as exit_code 1
        self.assertEqual(result.exit_code, 1)
        self.assertIn("❌ FAILED", result.output)


if __name__ == "__main__":
    unittest.main()
