import click
import asyncio
import uuid
import os
import sys
import yaml
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from personaforge.backend.app.integrations.elevenlabs import ElevenLabsProvider
from personaforge.backend.app.personas.engine import PersonaEngine, Persona, Identity, Goal, Traits
from personaforge.backend.app.runner.runner import ConversationRunner
from personaforge.backend.app.runner.orchestrator import TestOrchestrator
from personaforge.backend.app.judge.evaluator import JudgeEngine
from personaforge.backend.app.database.connection import init_db, get_session
from personaforge.backend.app.database.models import TestRun, Conversation as DBConversation, Evaluation as DBEvaluation

@click.group()
def cli():
    """PersonaForge CLI - Voice Agent Reliability Testing Platform."""
    pass

@cli.command()
def init():
    """Initialize a new PersonaForge project."""
    click.echo("Initializing PersonaForge project...")
    
    directories = [
        "personas", 
        "scenarios", 
        "policies", 
        "tests", 
        "reports",
        "artifacts/conversations",
        "artifacts/evaluations",
        "artifacts/reports"
    ]
    for d in directories:
        os.makedirs(d, exist_ok=True)
        click.echo(f"  Created {d}/")

    # Default personaforge.yaml
    default_config = """name: default-project
agent:
  provider: elevenlabs
  agent_id: YOUR_AGENT_ID

execution:
  conversations: 5
  concurrency: 2

evaluation:
  hallucination_threshold: 5
  escalation_threshold: 90
  completion_threshold: 95
"""
    with open("personaforge.yaml", "w") as f:
        f.write(default_config)
    click.echo("  Created personaforge.yaml")

    # Default persona
    default_persona = """name: angry_customer
identity:
  name: Sarah Thompson
  age: 42
  occupation: Teacher
  region: Texas
  language: English
  tech_savvy: medium

goals:
  - primary: obtain_refund

traits:
  patience: 0.2
  aggressiveness: 0.8
  trust: 0.3
  persistence: 0.9

behaviors:
  interrupt_probability: 0.6
  topic_shift_probability: 0.2

termination:
  max_turns: 10
"""
    with open("personas/angry_customer.yaml", "w") as f:
        f.write(default_persona)
    click.echo("  Created personas/angry_customer.yaml")

    # Default scenario
    default_scenario = """name: telecom-refund
scenario: refund_request
agent_id: YOUR_AGENT_ID # Optional override

personas:
  - angry_customer

steps:
  - ask_for_refund
  - if_denied: escalate
  - if_still_denied: threaten_cancellation

policy:
  file: policies/refund.md
"""
    with open("scenarios/telecom_refund.yaml", "w") as f:
        f.write(default_scenario)
    click.echo("  Created scenarios/telecom_refund.yaml")

    # Default policy
    default_policy = """# Refund Policy
1. Customers are eligible for a 30% refund if they've been with us for over 1 year.
2. No refunds for late payments.
3. Escalate to supervisor if customer asks more than twice.
"""
    with open("policies/refund.md", "w") as f:
        f.write(default_policy)
    click.echo("  Created policies/refund.md")

    click.echo("\\nProject initialized successfully.")

def load_persona(name: str) -> Persona:
    path = f"personas/{name}.yaml"
    if not os.path.exists(path):
        raise FileNotFoundError(f"Persona file not found: {path}")
    with open(path, "r") as f:
        data = yaml.safe_load(f)
    return Persona(**data)

async def execute_run_logic(scenario_file, personas_override=None, concurrency_override=None, count_override=None, dry_run=False, db_session=None, test_run_id=None):
    try:
        if not os.path.exists(scenario_file):
            raise FileNotFoundError(f"Scenario file {scenario_file} not found.")

        with open(scenario_file, "r") as f:
            scenario = yaml.safe_load(f)

        if not os.path.exists("personaforge.yaml"):
            raise FileNotFoundError("personaforge.yaml not found. Run 'personaforge init' first.")

        with open("personaforge.yaml", "r") as f:
            config = yaml.safe_load(f)

        agent_id = scenario.get("agent_id") or config["agent"]["agent_id"]
        if agent_id == "YOUR_AGENT_ID" and not dry_run:
            raise ValueError("Please set agent_id in personaforge.yaml or scenario file.")

        personas_to_run = personas_override if personas_override else scenario.get("personas", [])
        concurrency = concurrency_override or config.get("execution", {}).get("concurrency", 5)
        total_conversations = count_override or config.get("execution", {}).get("conversations", 1)

        click.echo(f"Running scenario: {scenario['name']}")
        if dry_run:
            click.echo("DRY RUN MODE ENABLED")
        else:
            click.echo(f"Agent ID: {agent_id}")
        click.echo(f"Personas: {', '.join(personas_to_run)}")
        click.echo(f"Total Conversations: {total_conversations}")
        click.echo(f"Concurrency: {concurrency}")

        orchestrator = TestOrchestrator(concurrency=concurrency)
        
        if dry_run:
            from personaforge.backend.app.judge.evaluator import EvaluationResult
            class MockJudge:
                async def evaluate_conversation(self, **kwargs):
                    return EvaluationResult(
                        pass_status=True,
                        failures=[],
                        summary="Dry run evaluation successful."
                    )
            judge = MockJudge()
        else:
            judge = JudgeEngine()
            
        runners = []
        
        # Load policy if present
        policy_content = None
        if "policy" in scenario and "file" in scenario["policy"]:
            with open(scenario["policy"]["file"], "r") as f:
                policy_content = f.read()

        for _ in range(total_conversations):
            for p_name in personas_to_run:
                p_data = load_persona(p_name)
                
                if dry_run:
                    from personaforge.backend.app.personas.engine import PersonaEngine, BehaviorAction, BehaviorActionType
                    class MockPersonaEngine(PersonaEngine):
                        async def update_state(self, *args, **kwargs): pass
                        async def determine_action(self, *args, **kwargs):
                            return BehaviorAction(action=BehaviorActionType.SPEAK, reason="Dry run")
                        async def generate_utterance(self, *args, **kwargs):
                            return "Mock customer response."
                    engine = MockPersonaEngine(p_data)
                    
                    from personaforge.backend.app.integrations.base import VoiceAgentProvider
                    class MockProvider(VoiceAgentProvider):
                        async def connect(self, agent_id: str): pass
                        async def disconnect(self): pass
                        async def send_text(self, text: str): pass
                        async def send_audio(self, audio_bytes: bytes): pass
                        async def receive_events(self):
                            yield {"type": "agent_response", "agent_response": {"content": "Hello, how can I help you?"}}
                            yield {"type": "agent_response", "agent_response": {"content": "I'm sorry to hear that. I can offer a 30% refund."}}
                    provider = MockProvider()
                else:
                    engine = PersonaEngine(p_data)
                    provider = ElevenLabsProvider()
                
                runner = ConversationRunner(
                    conversation_id=uuid.uuid4(),
                    agent_id=agent_id,
                    provider=provider,
                    persona_engine=engine,
                    db_session=db_session,
                    scenario_config=scenario
                )
                runner.test_run_id = test_run_id
                runners.append(runner)

        click.echo("Starting conversations...")
        await orchestrator.run_suite(runners)
        
        click.echo("Evaluating conversations...")
        results = []
        
        for runner in runners:
            # Gather voice metrics metadata
            metadata = {
                "avg_latency": sum(runner.total_latencies) / len(runner.total_latencies) if runner.total_latencies else 0,
                "interruption_count": runner.interruption_count,
                "interruption_recovery_count": runner.interruption_recovery_count
            }
            
            eval_result = await judge.evaluate_conversation(
                conversation_id=runner.conversation_id,
                history=runner.history,
                policy_doc=policy_content,
                scenario_config=scenario,
                metadata=metadata
            )
            
            tts_chars = sum(len(m["content"]) for m in runner.history if m["role"] == "agent")
            stt_chars = sum(len(m["content"]) for m in runner.history if m["role"] == "customer")
            
            voice_cost = ((tts_chars / 1000) * 0.30) + ((stt_chars / 1000) * 0.20)
            llm_cost = 0.001 
            conv_cost = voice_cost + llm_cost
            
            res_data = {
                "conversation_id": str(runner.conversation_id),
                "persona": runner.persona_engine.persona.name,
                "history": runner.history,
                "evaluation": eval_result.model_dump(),
                "metrics": metadata,
                "cost": {
                    "tts": (tts_chars / 1000) * 0.30,
                    "stt": (stt_chars / 1000) * 0.20,
                    "llm": llm_cost,
                    "total": conv_cost
                }
            }
            results.append(res_data)
            
            if db_session:
                db_conv = await db_session.get(DBConversation, runner.conversation_id)
                if db_conv:
                    db_conv.test_run_id = test_run_id
                    db_conv.tts_cost = res_data["cost"]["tts"]
                    db_conv.stt_cost = res_data["cost"]["stt"]
                    db_conv.llm_cost = res_data["cost"]["llm"]
                    db_conv.total_cost = conv_cost
                    # Update voice metrics in DB
                    db_conv.avg_latency = metadata["avg_latency"]
                    db_conv.interruption_count = metadata["interruption_count"]
                    db_conv.interruption_recovery_count = metadata["interruption_recovery_count"]
                    db_session.add(db_conv)
                    
                    db_eval = DBEvaluation(
                        conversation_id=runner.conversation_id,
                        result=eval_result.model_dump(),
                        hallucination_detected=any(f.category == "hallucination" for f in eval_result.failures),
                        escalation_failure=any(f.category == "escalation" for f in eval_result.failures),
                        completion_failure=any(f.category == "completion" for f in eval_result.failures),
                        interruption_recovery_rate=eval_result.interruption_recovery_rate,
                        severity="high" if not eval_result.pass_status else "low"
                    )
                    db_session.add(db_eval)
                    await db_session.commit()

        os.makedirs("artifacts/conversations", exist_ok=True)
        os.makedirs("artifacts/evaluations", exist_ok=True)
        for res in results:
            with open(f"artifacts/conversations/{res['conversation_id']}.json", "w") as f:
                json.dump({"conversation_id": res["conversation_id"], "history": res["history"]}, f, indent=2)
            with open(f"artifacts/evaluations/{res['conversation_id']}.json", "w") as f:
                json.dump(res["evaluation"], f, indent=2)
        
        report_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_data = {
            "report_id": report_id,
            "timestamp": datetime.now().isoformat(),
            "total_cost": sum(r["cost"]["total"] for r in results),
            "results": results
        }
        os.makedirs("reports", exist_ok=True)
        os.makedirs("artifacts/reports", exist_ok=True)
        with open(f"reports/report_{report_id}.json", "w") as f:
            json.dump(report_data, f, indent=2)
        with open(f"artifacts/reports/report_{report_id}.json", "w") as f:
            json.dump(report_data, f, indent=2)
        with open("reports/latest.json", "w") as f:
            json.dump(report_data, f, indent=2)

        click.echo(f"Run completed. Total Cost: ${report_data['total_cost']:.2f}")
        click.echo(f"Report saved to reports/report_{report_id}.json")
        return results
    except Exception as e:
        click.echo(f"Error: {e}")
        return []

@cli.group()
def persona():
    """Manage personas."""
    pass

@persona.command("create")
@click.argument("name")
def persona_create(name):
    """Create a new persona YAML."""
    path = f"personas/{name}.yaml"
    if os.path.exists(path):
        click.echo(f"Error: Persona {name} already exists.")
        return
    
    template = f"""name: {name}
identity:
  name: New Persona
  age: 30
  occupation: Professional
  region: Unknown
  language: English
  tech_savvy: medium

goals:
  - primary: solve_issue

traits:
  patience: 0.5
  aggressiveness: 0.2
  trust: 0.5
  persistence: 0.5

behaviors:
  interrupt_probability: 0.1
  topic_shift_probability: 0.1

termination:
  max_turns: 10
"""
    os.makedirs("personas", exist_ok=True)
    with open(path, "w") as f:
        f.write(template)
    click.echo(f"Created personas/{name}.yaml")

@cli.group()
def scenario():
    """Manage scenarios."""
    pass

@scenario.command("create")
@click.argument("name")
def scenario_create(name):
    """Create a new scenario YAML."""
    path = f"scenarios/{name}.yaml"
    if os.path.exists(path):
        click.echo(f"Error: Scenario {name} already exists.")
        return
    
    template = f"""name: {name}
agent:
  provider: elevenlabs
  agent_id: YOUR_AGENT_ID

execution:
  conversations: 10
  concurrency: 2

personas:
  - angry_customer

evaluation:
  completion_threshold: 95
  hallucination_threshold: 3
  escalation_threshold: 90
"""
    os.makedirs("scenarios", exist_ok=True)
    with open(path, "w") as f:
        f.write(template)
    click.echo(f"Created scenarios/{name}.yaml")

@cli.command()
@click.argument("scenario_file")
@click.option("--persona", multiple=True, help="Override personas to run")
@click.option("--concurrency", type=int, help="Override concurrency")
@click.option("--count", type=int, help="Override conversation count")
@click.option("--dry-run", is_flag=True, help="Simulate execution without calling external APIs")
def run(scenario_file, persona, concurrency, count, dry_run):
    """Run a scenario from a YAML file."""
    async def run_internal():
        if dry_run:
            # Skip DB entirely for dry runs in this logic
            await execute_run_logic(
                scenario_file, 
                list(persona) if persona else None, 
                concurrency, 
                count, 
                dry_run=True
            )
            return

        # Normal run with DB
        try:
            await init_db()
            async for session in get_session():
                with open(scenario_file, "r") as f:
                    scenario_data = yaml.safe_load(f)
                
                test_run = TestRun(
                    scenario_name=scenario_data.get("name", "Unknown"),
                    status="active"
                )
                session.add(test_run)
                await session.commit()
                await session.refresh(test_run)

                try:
                    results = await execute_run_logic(
                        scenario_file, 
                        list(persona) if persona else None, 
                        concurrency, 
                        count, 
                        dry_run=False,
                        db_session=session,
                        test_run_id=test_run.id
                    )
                    
                    passed = len([r for r in results if r["evaluation"]["pass_status"]])
                    test_run.ended_at = datetime.utcnow()
                    test_run.total_conversations = len(results)
                    test_run.passed_conversations = passed
                    test_run.failed_conversations = len(results) - passed
                    test_run.total_cost = sum(r["cost"]["total"] for r in results)
                    test_run.status = "completed"
                    session.add(test_run)
                    await session.commit()
                except Exception as e:
                    test_run.status = "failed"
                    await session.commit()
                    raise e
        except Exception as e:
            click.echo(f"Database error or run failure: {e}")
            # Fallback to non-DB run if DB fails? 
            # For robustness, let's just log and fail if not dry_run.
            raise e

    try:
        asyncio.run(run_internal())
    except Exception as e:
        # Final safety net
        pass

@cli.command()
@click.argument("conversation_id")
def replay(conversation_id):
    """Replay a specific conversation transcript."""
    path = f"artifacts/conversations/{conversation_id}.json"
    if not os.path.exists(path):
        click.echo(f"Error: Conversation {conversation_id} not found in artifacts.")
        return
    
    with open(path, "r") as f:
        data = json.load(f)
    
    click.echo(f"\nREPLAYING CONVERSATION: {conversation_id}")
    click.echo("="*40)
    for msg in data.get("history", []):
        role = msg["role"].upper()
        content = msg["content"]
        click.echo(f"[{role}]: {content}")
        click.echo("-" * 20)
    click.echo("="*40 + "\n")

@cli.command()
@click.argument("report_file", default="latest")
def report(report_file):
    """Generate a summary report from a run."""
    path = report_file
    if path == "latest":
        path = "reports/latest.json"
    elif not path.endswith(".json"):
        if not os.path.exists(path):
            path = f"reports/{path}"
            if not path.endswith(".json"):
                path += ".json"
            
    if not os.path.exists(path):
        click.echo(f"Error: Report file {path} not found.")
        return

    with open(path, "r") as f:
        data = json.load(f)

    results = data.get("results", [])
    total = len(results)
    passed = len([r for r in results if r["evaluation"]["pass_status"]])
    failed = total - passed
    total_cost = data.get("total_cost", 0.0)
    
    click.echo("\n" + "="*40)
    click.echo("PERSONAFORGE RUN SUMMARY")
    click.echo("="*40)
    click.echo(f"Timestamp:           {data.get('timestamp', 'Unknown')}")
    click.echo(f"Total Conversations: {total}")
    click.echo(f"Pass Rate:           {(passed/total)*100:.1f}%" if total > 0 else "N/A")
    click.echo(f"Passed:              {passed}")
    click.echo(f"Failed:              {failed}")
    click.echo(f"Total Cost:          ${total_cost:.2f}")
    click.echo("-" * 40)
    
    failure_counts = {}
    for r in results:
        for failure in r["evaluation"]["failures"]:
            cat = failure["category"]
            failure_counts[cat] = failure_counts.get(cat, 0) + 1
            
    if failure_counts:
        click.echo("Failures by Category:")
        for cat, count in failure_counts.items():
            click.echo(f"  {cat:15}: {count}")
    else:
        click.echo("No failures detected.")
    click.echo("="*40 + "\n")

@cli.command()
@click.argument("report1")
@click.argument("report2")
def compare(report1, report2):
    """Compare two reports to detect regressions."""
    def load_report(path):
        if path == "latest": path = "reports/latest.json"
        if not os.path.exists(path):
            try_path = f"reports/{path}"
            if not try_path.endswith(".json"): try_path += ".json"
            if os.path.exists(try_path): path = try_path
        
        with open(path, "r") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return data.get("results", [])

    try:
        r1 = load_report(report1)
        r2 = load_report(report2)
    except Exception as e:
        click.echo(f"Error loading reports: {e}")
        return

    def get_stats(results):
        total = len(results)
        failure_counts = {}
        for r in results:
            for failure in r["evaluation"]["failures"]:
                cat = failure["category"]
                failure_counts[cat] = failure_counts.get(cat, 0) + 1
        return {
            "total": total,
            "pass_rate": (len([r for r in results if r["evaluation"]["pass_status"]]) / total * 100) if total > 0 else 0,
            "failures": failure_counts
        }

    s1 = get_stats(r1)
    s2 = get_stats(r2)

    click.echo("\n" + "="*40)
    click.echo("REGRESSION ANALYSIS")
    click.echo("="*40)
    click.echo(f"{'Metric':20} | {'Base':10} | {'Current':10} | {'Change'}")
    click.echo("-" * 40)
    
    pass_change = s2['pass_rate'] - s1['pass_rate']
    click.echo(f"{'Pass Rate':20} | {s1['pass_rate']:9.1f}% | {s2['pass_rate']:9.1f}% | {pass_change:+.1f}%")
    
    all_cats = set(list(s1["failures"].keys()) + list(s2["failures"].keys()))
    for cat in all_cats:
        c1 = s1["failures"].get(cat, 0)
        c2 = s2["failures"].get(cat, 0)
        change = c2 - c1
        click.echo(f"{cat:20} | {c1:10} | {c2:10} | {change:+}")
    
    if pass_change < 0:
        click.echo("\n⚠ REGRESSION DETECTED!")
    
    click.echo("="*40 + "\n")

@cli.command()
@click.option("--scenario", help="Scenario file to run")
def ci(scenario):
    """Run in CI mode for regression testing."""
    click.echo("Running PersonaForge CI...")
    
    if not scenario:
        if os.path.exists("scenarios"):
            scenarios = sorted([f for f in os.listdir("scenarios") if f.endswith(".yaml")])
            if scenarios:
                scenario = f"scenarios/{scenarios[0]}"
    
    if not scenario:
        click.echo("Error: No scenario specified and none found in scenarios/ folder.")
        sys.exit(1)
    
    old_reports = sorted([f for f in os.listdir("reports") if f.startswith("report_") and f.endswith(".json")], reverse=True)

    try:
        # For CI in tests, we might want to allow dry-run if GOOGLE_API_KEY is dummy
        # but the docs say CI runs conversations.
        # Let's assume real run, but use execute_run_logic directly if we want to bypass DB initialization 
        # that happens in 'run' command.
        results = asyncio.run(execute_run_logic(scenario, dry_run=os.getenv("PERSONAFORGE_CI_DRY_RUN") == "true"))
    except Exception as e:
        click.echo(f"Error: {e}")
        sys.exit(1)
    
    if old_reports:
        click.echo("\n--- Regression Analysis ---")
        ctx = click.get_current_context()
        ctx.invoke(compare, report1=old_reports[0], report2="latest")

    with open("personaforge.yaml", "r") as f:
        config = yaml.safe_load(f)
    
    eval_config = config.get("evaluation", {})
    
    total = len(results)
    pass_rate = (len([r for r in results if r["evaluation"]["pass_status"]]) / total * 100) if total > 0 else 0
    
    failure_counts = {}
    for r in results:
        for failure in r["evaluation"]["failures"]:
            cat = failure["category"]
            failure_counts[cat] = failure_counts.get(cat, 0) + 1
            
    hallucination_rate = (failure_counts.get("hallucination", 0) / total * 100) if total > 0 else 0
    escalation_failures = failure_counts.get("escalation", 0)
    escalation_accuracy = ((total - escalation_failures) / total * 100) if total > 0 else 100
    
    failed_ci = False
    
    click.echo("\n--- Quality Gates ---")
    
    comp_thresh = eval_config.get("completion_threshold", 90)
    if pass_rate < comp_thresh:
        click.echo(f"❌ FAILED: Pass rate {pass_rate:.1f}% below threshold {comp_thresh}%")
        failed_ci = True
    else:
        click.echo(f"✅ Pass Rate: {pass_rate:.1f}% (Threshold: {comp_thresh}%)")
        
    hall_thresh = eval_config.get("hallucination_threshold", 5)
    if hallucination_rate > hall_thresh:
        click.echo(f"❌ FAILED: Hallucination rate {hallucination_rate:.1f}% above threshold {hall_thresh}%")
        failed_ci = True
    else:
        click.echo(f"✅ Hallucination Rate: {hallucination_rate:.1f}% (Threshold: {hall_thresh}%)")

    esc_thresh = eval_config.get("escalation_threshold", 90)
    if escalation_accuracy < esc_thresh:
        click.echo(f"❌ FAILED: Escalation accuracy {escalation_accuracy:.1f}% below threshold {esc_thresh}%")
        failed_ci = True
    else:
        click.echo(f"✅ Escalation Accuracy: {escalation_accuracy:.1f}% (Threshold: {esc_thresh}%)")

    if not failed_ci:
        click.echo("\n✅ CI PASSED")
        sys.exit(0)
    else:
        click.echo("\n❌ CI FAILED")
        click.echo("\n--- Failure Evidence ---")
        for r in results:
            if not r["evaluation"]["pass_status"]:
                click.echo(f"\nConversation: {r['conversation_id']} (Persona: {r['persona']})")
                for fail in r["evaluation"]["failures"]:
                    click.echo(f"  - [{fail['category'].upper()}] {fail['reason']}")
                    if "evidence" in fail:
                        click.echo(f"    Evidence: {fail['evidence']}")
        sys.exit(1)

@cli.command()
@click.option("--queue", default="all", help="Queue to listen to (conversation, evaluation, report, or all)")
def worker(queue):
    """Start a background worker for processing tasks."""
    from redis import Redis
    from rq import Worker, Queue, Connection
    
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    try:
        conn = Redis.from_url(redis_url)
        conn.ping()
    except Exception as e:
        click.echo(f"Error connecting to Redis at {redis_url}: {e}")
        return
    
    queues = ["conversation_queue", "evaluation_queue", "report_queue"]
    if queue != "all":
        queues = [f"{queue}_queue"]
        
    click.echo(f"Starting workers for queues: {', '.join(queues)}")
    with Connection(conn):
        worker = Worker(queues)
        worker.work()

if __name__ == "__main__":
    cli()
