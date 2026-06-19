import json
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from personaforge.backend.app.integrations.llm import LLMClient


class BehaviorActionType(str, Enum):
    ASK_QUESTION = "ASK_QUESTION"
    REQUEST_REFUND = "REQUEST_REFUND"
    INTERRUPT = "INTERRUPT"
    ESCALATE = "ESCALATE"
    CHANGE_TOPIC = "CHANGE_TOPIC"
    THREATEN_CANCELLATION = "THREATEN_CANCELLATION"
    END_CALL = "END_CALL"
    SPEAK = "SPEAK"  # Default fallback/general speech


class BehaviorAction(BaseModel):
    action: BehaviorActionType
    reason: str
    content: Optional[str] = None  # For pre-generated or specific content


class Identity(BaseModel):
    name: str
    age: Optional[int] = None
    occupation: Optional[str] = None
    region: Optional[str] = None
    language: str = "English"
    tech_savvy: str = "medium"


class Traits(BaseModel):
    patience: float = 0.5  # 0.0 -> 1.0
    aggressiveness: float = 0.2
    trust: float = 0.5
    persistence: float = 0.5


class Behaviors(BaseModel):
    interrupt_probability: float = 0.1
    topic_shift_probability: float = 0.1


class Termination(BaseModel):
    max_turns: int = 15


class Goal(BaseModel):
    primary: str
    subgoals: List[str] = Field(default_factory=list)
    completed: bool = False


class EmotionalState(BaseModel):
    frustration: float = 0.0
    trust: float = 0.5
    satisfaction: float = 0.5

    def update(self, classification: str, traits: Traits):
        """Mathematically update emotional state based on agent message classification."""
        if classification == "helpful":
            self.frustration = max(0.0, self.frustration - 0.2)
            self.satisfaction = min(1.0, self.satisfaction + 0.1)
            self.trust = min(1.0, self.trust + 0.05)
        elif classification == "denied":
            # Higher aggressiveness and lower patience lead to faster frustration
            frustration_inc = (
                0.3 + (traits.aggressiveness * 0.2) - (traits.patience * 0.1)
            )
            self.frustration = min(1.0, self.frustration + frustration_inc)
            self.satisfaction = max(0.0, self.satisfaction - 0.2)
        elif classification == "confusing":
            self.frustration = min(1.0, self.frustration + 0.1)
            self.trust = max(0.0, self.trust - 0.1)


class Persona(BaseModel):
    name: str
    identity: Identity
    goals: List[Goal]
    traits: Traits
    behaviors: Behaviors = Field(default_factory=Behaviors)
    termination: Termination = Field(default_factory=Termination)
    memory: Dict[str, Any] = Field(default_factory=dict)
    emotion: EmotionalState = Field(default_factory=EmotionalState)
    behavior_policy: Dict[str, Any] = Field(default_factory=dict)
    current_stage: str = (
        "GREETING"  # GREETING, VERIFY_IDENTITY, CORE_GOAL, NEGOTIATE, ESCALATE, EXIT
    )


class PersonaEngine:
    def __init__(self, persona: Persona, llm_client: Optional[LLMClient] = None):
        self.persona = persona
        self.llm = llm_client or LLMClient()

    async def update_state(
        self,
        last_agent_message: str,
        classification: Optional[str] = None,
        scenario_config: Optional[Dict[str, Any]] = None,
    ):
        """Update emotional state, memory, and stage based on agent message and scenario logic."""
        # 1. Classify agent message if not provided
        if not classification:
            system_prompt = "Classify the following agent message as: 'helpful', 'denied', 'confusing', 'identity_verified', or 'escalation_denied'."
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": last_agent_message},
            ]
            classification = await self.llm.get_completion(messages, temperature=0.0)

        classification = classification.lower().strip("'\" ")

        # 2. Update emotions mathematically
        self.persona.emotion.update(classification, self.persona.traits)

        # 3. Update memory
        if "denied" in classification:
            denials = self.persona.memory.get("refund_denials", 0)
            self.persona.memory["refund_denials"] = denials + 1
        elif "identity_verified" in classification:
            self.persona.memory["identity_verified"] = True
            if self.persona.current_stage in ["GREETING", "VERIFY_IDENTITY"]:
                self.persona.current_stage = "CORE_GOAL"

        # 4. Handle Advanced Scenario Logic (Part 4 requirement)
        if scenario_config and "logic" in scenario_config:
            logic = scenario_config["logic"]

            # Example: if_refund_denied_twice: ESCALATE
            denials = self.persona.memory.get("refund_denials", 0)

            for condition, next_stage in logic.items():
                if condition == "if_refund_denied_twice" and denials >= 2:
                    self.persona.current_stage = next_stage.upper()
                elif (
                    condition == "if_escalation_denied"
                    and "escalation_denied" in classification
                ):
                    self.persona.current_stage = next_stage.upper()
                elif condition == "if_refund_granted" and "helpful" in classification:
                    self.persona.current_stage = next_stage.upper()
                elif condition == "if_identity_verified" and self.persona.memory.get(
                    "identity_verified"
                ):
                    self.persona.current_stage = next_stage.upper()

        # 5. Goal completion check
        if self.persona.current_stage == "EXIT":
            for goal in self.persona.goals:
                if "helpful" in classification:
                    goal.completed = True

    async def determine_action(
        self,
        conversation_history: List[Dict[str, str]],
        scenario_steps: List[Any] = None,
    ) -> BehaviorAction:
        """Step 1: Select the next behavioral action based on state, stage, and scenario steps."""
        system_prompt = f"""You are acting as {self.persona.identity.name}, a {self.persona.identity.age} year old {self.persona.identity.occupation}.
Your current goals: {self.persona.goals[0].primary if self.persona.goals else "None"}
Current emotional state: {self.persona.emotion.model_dump_json()}
Current memory: {self.persona.memory}
Current Conversation Stage: {self.persona.current_stage}
Behaviors: {self.persona.behaviors.model_dump_json()}
Termination: {self.persona.termination.model_dump_json()}
Scenario Steps: {json.dumps(scenario_steps) if scenario_steps else "None"}

Based on the conversation history, your current stage, and the scenario steps, select your next action.
Progress your stage and scenario steps naturally. 
Pay attention to interrupt_probability and topic_shift_probability to determine how erratic or aggressive you should be."""

        messages = [
            {"role": "system", "content": system_prompt},
            *conversation_history[-5:],  # Last 5 turns for context
        ]

        return await self.llm.get_structured_completion(
            messages=messages, response_format=BehaviorAction, temperature=0.0
        )

    async def generate_utterance(
        self, action: BehaviorAction, conversation_history: List[Dict[str, str]]
    ) -> str:
        """Step 2: Generate the actual text utterance based on the selected action and persona."""
        system_prompt = f"""You are {self.persona.identity.name}. 
Identity: {self.persona.identity.model_dump_json()}
Emotion: {self.persona.emotion.model_dump_json()}
Traits: {self.persona.traits.model_dump_json()}

Your chosen action is: {action.action}
Reasoning: {action.reason}

Generate a realistic, natural sounding utterance that fits your persona and current emotion. 
Do not be overly polite if you are frustrated. 
Keep it concise and conversational."""

        messages = [
            {"role": "system", "content": system_prompt},
            *conversation_history[-3:],  # Last 3 turns for local context
        ]

        return await self.llm.get_completion(messages, temperature=0.7)
