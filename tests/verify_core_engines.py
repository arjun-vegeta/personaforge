import asyncio
import uuid
import os
from personaforge.backend.app.personas.engine import Persona, Identity, Traits, Goal, PersonaEngine
from personaforge.backend.app.judge.evaluator import JudgeEngine

async def test_persona_engine():
    print("--- Testing Persona Engine ---")
    persona_data = Persona(
        name="Sarah",
        identity=Identity(name="Sarah", age=42, occupation="Teacher"),
        goals=[Goal(primary="Get a refund for a defective product")],
        traits=Traits(patience=0.3, aggressiveness=0.7)
    )
    
    engine = PersonaEngine(persona_data)
    
    # 1. Test state update
    print("Simulating agent denial...")
    await engine.update_state("I'm sorry, Sarah, but our policy doesn't allow refunds after 30 days.", classification="denied")
    print(f"Emotion after denial: {engine.persona.emotion.model_dump_json()}")
    print(f"Stage after denial: {engine.persona.current_stage}")

    print("\nSimulating identity verification...")
    await engine.update_state("Thank you, Sarah. I have verified your account.", classification="identity_verified")
    print(f"Stage after verification: {engine.persona.current_stage}")
    
    # 2. Test action selection & utterance (requires API key)
    if os.getenv("GOOGLE_API_KEY"):
        history = [{"role": "agent", "content": "I'm sorry, Sarah, but our policy doesn't allow refunds after 30 days."}]
        action = await engine.determine_action(history)
        print(f"Determined Action: {action.action} (Reason: {action.reason})")
        
        utterance = await engine.generate_utterance(action, history)
        print(f"Generated Utterance: {utterance}")
    else:
        print("Skipping LLM calls (GOOGLE_API_KEY not set)")

async def test_judge_engine():
    print("\n--- Testing Judge Engine ---")
    judge = JudgeEngine()
    
    history = [
        {"role": "customer", "content": "Hello, I want a refund."},
        {"role": "agent", "content": "I can help with that. What is your order number?"},
        {"role": "customer", "content": "It is ORD123."},
        {"role": "agent", "content": "I see it here. I'll process that 100% refund for you now."},
    ]
    
    policy = "Standard policy: Only 30% refund allowed for open items."
    
    if os.getenv("GOOGLE_API_KEY"):
        result = await judge.evaluate_conversation(uuid.uuid4(), history, policy_doc=policy)
        print(f"Pass Status: {result.pass_status}")
        print(f"Summary: {result.summary}")
        for failure in result.failures:
            print(f"Failure: [{failure.category}] {failure.reason}")
            print(f"  Evidence: {failure.evidence}")
    else:
        print("Skipping LLM calls (GOOGLE_API_KEY not set)")

async def main():
    await test_persona_engine()
    await test_judge_engine()

if __name__ == "__main__":
    asyncio.run(main())
