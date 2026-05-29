import asyncio
import uuid
import yaml
import os
import json
from datetime import datetime
from personaforge.backend.app.personas.engine import PersonaEngine, Persona
from personaforge.backend.app.runner.runner import ConversationRunner
from personaforge.backend.app.integrations.elevenlabs import ElevenLabsProvider
from personaforge.backend.app.judge.evaluator import JudgeEngine

async def _run_conversation_internal(scenario_config, persona_name, agent_id, dry_run=False):
    """Internal async implementation of run_conversation_task."""
    # Load persona
    persona_path = f"personas/{persona_name}.yaml"
    if not os.path.exists(persona_path):
        # Try searching in project root or relative to CWD
        pass
        
    with open(persona_path, "r") as f:
        p_data = yaml.safe_load(f)
    persona = Persona(**p_data)
    engine = PersonaEngine(persona)
    
    if dry_run:
        from personaforge.backend.app.integrations.base import VoiceAgentProvider
        class MockProvider(VoiceAgentProvider):
            async def connect(self, agent_id: str): pass
            async def disconnect(self): pass
            async def send_text(self, text: str): pass
            async def send_audio(self, audio_bytes: bytes): pass
            async def receive_events(self):
                # Fixed mock sequence
                yield {"type": "agent_response", "agent_response": {"content": "Hello, how can I help you today?"}}
                await asyncio.sleep(0.1)
                yield {"type": "agent_response", "agent_response": {"content": "I understand you are looking for a refund."}}
                await asyncio.sleep(0.1)
                yield {"type": "agent_response", "agent_response": {"content": "I have checked our records and unfortunately, I cannot process a refund at this time."}}
        provider = MockProvider()
    else:
        provider = ElevenLabsProvider()
        
    runner = ConversationRunner(
        conversation_id=uuid.uuid4(),
        agent_id=agent_id,
        provider=provider,
        persona_engine=engine,
        scenario_config=scenario_config
    )
    
    await runner.run()
    
    # Save transcript artifact immediately
    os.makedirs("artifacts/conversations", exist_ok=True)
    artifact_data = {
        "conversation_id": str(runner.conversation_id),
        "history": runner.history,
        "persona": persona_name,
        "timestamp": datetime.now().isoformat()
    }
    with open(f"artifacts/conversations/{runner.conversation_id}.json", "w") as f:
        json.dump(artifact_data, f, indent=2)
        
    return artifact_data

def run_conversation_task(scenario_config, persona_name, agent_id, dry_run=False):
    """RQ task to run a single conversation."""
    return asyncio.run(_run_conversation_internal(scenario_config, persona_name, agent_id, dry_run))

async def _run_evaluation_internal(conversation_id, history, policy_doc, scenario_config):
    """Internal async implementation of run_evaluation_task."""
    judge = JudgeEngine()
    eval_result = await judge.evaluate_conversation(
        conversation_id=uuid.UUID(conversation_id) if isinstance(conversation_id, str) else conversation_id,
        history=history,
        policy_doc=policy_doc,
        scenario_config=scenario_config
    )
    
    # Save evaluation artifact
    os.makedirs("artifacts/evaluations", exist_ok=True)
    with open(f"artifacts/evaluations/{conversation_id}.json", "w") as f:
        json.dump(eval_result.model_dump(), f, indent=2)
        
    return eval_result.model_dump()

def run_evaluation_task(conversation_id, history, policy_doc, scenario_config):
    """RQ task to evaluate a completed conversation."""
    return asyncio.run(_run_evaluation_internal(conversation_id, history, policy_doc, scenario_config))

def run_report_task(run_results, report_id):
    """RQ task to aggregate results into a report."""
    total_cost = 0.0
    for r in run_results:
        # Simplified cost calc (matching CLI logic)
        chars = sum(len(m["content"]) for m in r["history"] if m["role"] == "agent")
        voice_cost = (chars / 1000) * 0.30
        llm_cost = 0.001
        total_cost += voice_cost + llm_cost
        
    report_data = {
        "report_id": report_id,
        "timestamp": datetime.now().isoformat(),
        "total_cost": total_cost,
        "results": run_results
    }
    
    os.makedirs("reports", exist_ok=True)
    report_path = f"reports/report_{report_id}.json"
    with open(report_path, "w") as f:
        json.dump(report_data, f, indent=2)
        
    # Update latest pointer
    with open("reports/latest.json", "w") as f:
        json.dump(report_data, f, indent=2)
        
    return report_path
