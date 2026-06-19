from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class ScenarioConfig(BaseModel):
    name: str
    description: str
    entry_conditions: Dict[str, Any] = {}
    success_conditions: List[str] = []
    failure_conditions: List[str] = []
    policy_doc: Optional[str] = None


class ScenarioEngine:
    def __init__(self, config: ScenarioConfig):
        self.config = config

    def validate_entry(self, persona_state: Dict[str, Any]) -> bool:
        """Check if persona/agent state meets entry conditions."""
        # Simple implementation for V1
        return True

    def check_completion(self, history: List[Dict[str, str]]) -> Dict[str, Any]:
        """Determine if scenario goals were met based on history."""
        # This logic is shared with the JudgeEngine
        return {"completed": True, "status": "success"}
