import asyncio
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlmodel.ext.asyncio.session import AsyncSession
from ..integrations.base import VoiceAgentProvider
from ..personas.engine import PersonaEngine
from ..database.models import Message, Conversation as DBConversation

class ConversationRunner:
    def __init__(
        self,
        conversation_id: uuid.UUID,
        agent_id: str,
        provider: VoiceAgentProvider,
        persona_engine: PersonaEngine,
        db_session: Optional[AsyncSession] = None,
        scenario_config: Optional[Dict[str, Any]] = None
    ):
        self.conversation_id = conversation_id
        self.agent_id = agent_id
        self.provider = provider
        self.persona_engine = persona_engine
        self.db_session = db_session
        self.scenario_config = scenario_config or {}
        self.history: List[Dict[str, str]] = []
        self.turn_count = 0
        self.is_running = False
        self.test_run_id: Optional[uuid.UUID] = None

    async def run(self):
        self.is_running = True
        
        # Create conversation record if db_session exists
        if self.db_session:
            db_conv = DBConversation(
                id=self.conversation_id,
                test_run_id=self.test_run_id,
                agent_id=uuid.UUID(self.agent_id) if "-" in self.agent_id else None, 
                status="active"
            )
            self.db_session.add(db_conv)
            try:
                await self.db_session.commit()
            except Exception:
                await self.db_session.rollback()
                self.db_session = None # Disable DB for this run if commit fails (e.g. no connection)

        await self.provider.connect(self.agent_id)
        
        try:
            async for event in self.provider.receive_events():
                if not self.is_running:
                    break
                
                await self.handle_event(event)
        finally:
            if self.db_session:
                # Update status
                db_conv = await self.db_session.get(DBConversation, self.conversation_id)
                if db_conv:
                    db_conv.status = "completed"
                    db_conv.ended_at = datetime.utcnow()
                    self.db_session.add(db_conv)
                    await self.db_session.commit()
            
            await self.provider.disconnect()

    async def handle_event(self, event: Dict[str, Any]):
        event_type = event.get("type")
        
        if event_type == "agent_response":
            content = event.get("agent_response", {}).get("content", "")
            if content:
                await self.add_message("agent", content)
                
                # Check for max turns
                if self.turn_count >= self.persona_engine.persona.termination.max_turns * 2: # roles: agent + customer
                    self.is_running = False
                    return

                # 1. Update persona state (emotions, memory) based on agent response
                await self.persona_engine.update_state(content, scenario_config=self.scenario_config)
                
                # 2. Step 1: Determine behavioral action
                scenario_steps = self.scenario_config.get("steps", [])
                action_result = await self.persona_engine.determine_action(self.history, scenario_steps)
                
                if action_result.action == "END_CALL":
                    self.is_running = False
                    return

                # 3. Step 2: Generate utterance based on action
                response_text = await self.persona_engine.generate_utterance(action_result, self.history)
                
                if response_text:
                    await self.add_message("customer", response_text)
                    # For POC, we send text. Later we'll send audio.
                    await self.provider.send_text(response_text)
        
        elif event_type == "conversation_initiation_metadata":
            # Start the conversation if needed, or wait for agent to speak first
            pass
        
        elif event_type == "audio":
            # We could store audio or handle alignment here
            pass

    async def add_message(self, role: str, content: str):
        self.turn_count += 1
        self.history.append({"role": role, "content": content})
        
        if self.db_session:
            msg = Message(
                conversation_id=self.conversation_id,
                role=role,
                content=content,
                turn_number=self.turn_count
            )
            self.db_session.add(msg)
            await self.db_session.commit()

    async def stop(self):
        self.is_running = False
