from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class Identity(BaseModel):
    name: str
    age: Optional[int] = None
    occupation: Optional[str] = None
    region: Optional[str] = None
    language: str = "English"
    tech_savvy: str = "medium"

class Traits(BaseModel):
    patience: float = 0.5
    aggressiveness: float = 0.2
    trust: float = 0.5
    persistence: float = 0.5
    traits_extra: Dict[str, Any] = Field(default_factory=dict)

class Goal(BaseModel):
    primary: str
    subgoals: List[str] = Field(default_factory=list)
    completed: bool = False

class Persona(BaseModel):
    name: str
    identity: Identity
    goals: List[Goal]
    traits: Traits
    behavior_policy: Dict[str, Any] = Field(default_factory=dict)
    memory: Dict[str, Any] = Field(default_factory=dict)
    emotion_state: Dict[str, float] = Field(default_factory=lambda: {"frustration": 0.0, "trust": 0.5, "satisfaction": 0.5})

class PersonaEngine:
    def __init__(self, persona: Persona):
        self.persona = persona

    async def determine_action(self, conversation_history: List[Dict[str, str]]) -> Dict[str, Any]:
        # This will later call an LLM to decide the next action
        # For POC, we'll return a simple action
        return {"action": "SPEAK", "content": "Hello, I need help with a refund."}

    async def update_state(self, last_agent_message: str):
        # Update emotion and memory based on agent message
        pass
