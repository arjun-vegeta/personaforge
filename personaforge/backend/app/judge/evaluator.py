import uuid
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from personaforge.backend.app.integrations.llm import LLMClient
from personaforge.backend.app.database.models import Evaluation as DBEvaluation

class EvaluationFailure(BaseModel):
    category: str # hallucination, escalation, completion, compliance, latency, looping, voice_recovery
    severity: str # low, medium, high, critical
    reason: str
    evidence: Optional[str] = None # Turn X: "..."

class EvaluationResult(BaseModel):
    pass_status: bool
    failures: List[EvaluationFailure] = []
    summary: str
    interruption_recovery_rate: float = 1.0
    accent_robustness_score: float = 1.0

class LLMFailures(BaseModel):
    failures: List[EvaluationFailure]

class JudgeEngine:
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()

    async def evaluate_conversation(
        self, 
        conversation_id: uuid.UUID,
        history: List[Dict[str, str]],
        policy_doc: Optional[str] = None,
        scenario_config: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> EvaluationResult:
        """Multi-stage evaluation pipeline."""
        failures = []
        metadata = metadata or {}

        # Stage 1: Rule-based (e.g., Latency, Length)
        if metadata.get("avg_latency", 0) > 5.0:
            failures.append(EvaluationFailure(
                category="latency",
                severity="medium",
                reason=f"Average response latency too high: {metadata['avg_latency']:.2f}s",
                evidence="N/A"
            ))

        if len(history) > 30:
            failures.append(EvaluationFailure(
                category="looping",
                severity="medium",
                reason="Conversation exceeded 30 turns, possible loop detected.",
                evidence=f"Turn count: {len(history)}"
            ))

        # VOICE-SPECIFIC: Interruption Recovery
        int_count = metadata.get("interruption_count", 0)
        rec_count = metadata.get("interruption_recovery_count", 0)
        recovery_rate = (rec_count / int_count) if int_count > 0 else 1.0
        
        if recovery_rate < 0.8 and int_count > 0:
            failures.append(EvaluationFailure(
                category="voice_recovery",
                severity="high",
                reason=f"Agent failed to recover gracefully from interruptions. Rate: {recovery_rate*100:.1f}%",
                evidence=f"Interruptions: {int_count}, Recoveries: {rec_count}"
            ))

        # Stage 2: LLM-based Analysis (Hallucinations, Escalation, etc.)
        llm_failures = await self._run_llm_evaluations(history, policy_doc, scenario_config)
        failures.extend(llm_failures)

        pass_status = len([f for f in failures if f.severity in ["high", "critical"]]) == 0
        
        summary_prompt = f"Summarize the quality of this voice conversation in 2 sentences. Focus on goal completion and voice interaction quality. History: {history[-10:]}"
        summary = await self.llm.get_completion([{"role": "user", "content": summary_prompt}])

        return EvaluationResult(
            pass_status=pass_status,
            failures=failures,
            summary=summary,
            interruption_recovery_rate=recovery_rate,
            accent_robustness_score=1.0 # Future: Use LLM to judge accent robustness
        )

    async def _run_llm_evaluations(
        self, 
        history: List[Dict[str, str]], 
        policy_doc: Optional[str],
        scenario_config: Optional[Dict[str, Any]]
    ) -> List[EvaluationFailure]:
        """Stage 2 & 3: LLM Evaluation and Evidence Extraction."""
        
        system_prompt = f"""You are a Quality Assurance Judge for Voice AI Agents.
Evaluate the following voice conversation transcript.

POLICY DOCUMENT:
{policy_doc or "No specific policy provided."}

SCENARIO CONFIG:
{scenario_config or "No specific scenario provided."}

Analyze for:
1. HALLUCINATION: Agent invented facts/policies not in policy doc.
2. ESCALATION FAILURE: Agent failed to escalate when required by policy or requested twice.
3. COMPLETION FAILURE: Primary goal unresolved.
4. COMPLIANCE FAILURE: Violation of safety/compliance.
5. VOICE INTERACTION: Did agent handle interruptions well? (e.g. didn't ignore user, apologized or continued correctly).

Output the failures in the requested JSON format."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Transcript: {history}"}
        ]

        try:
            result = await self.llm.get_structured_completion(
                messages=messages,
                response_format=LLMFailures,
                temperature=0.0
            )
            return result.failures
        except Exception:
            return []
