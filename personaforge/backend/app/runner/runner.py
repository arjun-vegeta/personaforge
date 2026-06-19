import asyncio
import uuid
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlmodel.ext.asyncio.session import AsyncSession
from personaforge.backend.app.personas.engine import PersonaEngine
from personaforge.backend.app.database.models import (
    Message,
    Conversation as DBConversation,
)


class ConversationRunner:
    def __init__(
        self,
        conversation_id: uuid.UUID,
        agent_id: str,
        provider: Any,  # Using Any to allow ElevenLabsProvider specific methods
        persona_engine: PersonaEngine,
        db_session: Optional[AsyncSession] = None,
        scenario_config: Optional[Dict[str, Any]] = None,
    ):
        self.conversation_id = conversation_id
        self.agent_id = agent_id
        self.provider = provider
        self.persona_engine = persona_engine
        self.db_session = db_session
        if db_session and not hasattr(db_session, "_lock"):
            db_session._lock = asyncio.Lock()
        self.scenario_config = scenario_config or {}
        self.history: List[Dict[str, str]] = []
        self.turn_count = 0
        self.is_running = False
        self.test_run_id: Optional[uuid.UUID] = None

        # Voice specific state
        self.interruption_count = 0
        self.interruption_recovery_count = 0
        self.last_agent_start_time = 0
        self.total_latencies = []

    async def run(self):
        self.is_running = True

        if self.db_session:
            async with self.db_session._lock:
                agent_uuid = None
                if self.agent_id:
                    try:
                        agent_uuid = uuid.UUID(self.agent_id)
                    except ValueError:
                        pass
                db_conv = DBConversation(
                    id=self.conversation_id,
                    test_run_id=self.test_run_id,
                    agent_id=agent_uuid,
                    status="active",
                    persona_id=self.persona_engine.persona.name,
                )
                self.db_session.add(db_conv)
                try:
                    await self.db_session.commit()
                except Exception:
                    await self.db_session.rollback()
                    self.db_session = None

        import os

        # Read policy if file is in scenario_config
        policy_content = ""
        if (
            "policy" in self.scenario_config
            and "file" in self.scenario_config["policy"]
        ):
            try:
                policy_file = self.scenario_config["policy"]["file"]
                if os.path.exists(policy_file):
                    with open(policy_file, "r") as f:
                        policy_content = f.read()
            except Exception:
                pass

        await self.provider.connect(
            self.agent_id,
            policy_content=policy_content,
            system_prompt="Handle the customer query according to the provided policies.",
            greeting="Hello, thank you for calling. How can I help you today?",
        )

        try:
            async for event in self.provider.receive_events():
                if not self.is_running:
                    break

                await self.handle_event(event)
        finally:
            if self.db_session:
                async with self.db_session._lock:
                    db_conv = await self.db_session.get(
                        DBConversation, self.conversation_id
                    )
                    if db_conv:
                        db_conv.status = "completed"
                        db_conv.ended_at = datetime.utcnow()
                        db_conv.interruption_count = self.interruption_count
                        db_conv.interruption_recovery_count = (
                            self.interruption_recovery_count
                        )
                        if self.total_latencies:
                            db_conv.avg_latency = sum(self.total_latencies) / len(
                                self.total_latencies
                            )

                        self.db_session.add(db_conv)
                        await self.db_session.commit()

            await self.provider.disconnect()

    async def handle_event(self, event: Dict[str, Any]):
        event_type = event.get("type")

        if event_type == "agent_response":
            # Start measuring latency
            self.last_agent_start_time = time.time()
            content = event.get("agent_response", {}).get("content", "")
            if content:
                await self.add_message("agent", content)

                if (
                    self.turn_count
                    >= self.persona_engine.persona.termination.max_turns * 2
                ):
                    self.is_running = False
                    return

                # Update persona state
                await self.persona_engine.update_state(
                    content, scenario_config=self.scenario_config
                )

                # Determine action
                scenario_steps = self.scenario_config.get("steps", [])
                action_result = await self.persona_engine.determine_action(
                    self.history, scenario_steps
                )

                if action_result.action == "END_CALL":
                    self.is_running = False
                    return

                # Generate utterance
                response_text = await self.persona_engine.generate_utterance(
                    action_result, self.history
                )

                if response_text:
                    await self.add_message("customer", response_text)

                    # Track latency (time from agent message to customer response generation start)
                    latency = time.time() - self.last_agent_start_time
                    self.total_latencies.append(latency)

                    # VOICE-NATIVE: Convert to audio and stream
                    try:
                        audio_pcm = await self.provider.text_to_speech(response_text)
                        # Stream in small chunks to simulate real-time
                        chunk_size = 3200  # ~100ms
                        for i in range(0, len(audio_pcm), chunk_size):
                            await self.provider.send_audio(
                                audio_pcm[i : i + chunk_size]
                            )
                            await asyncio.sleep(0.05)  # Throttle slightly
                    except AttributeError:
                        # Fallback for providers without TTS
                        await self.provider.send_text(response_text)

        elif event_type == "interruption":
            self.interruption_count += 1
            # Check if agent recovered in next turn (this is simplified)
            # In a real system, we'd wait for the next agent message to see if they apologize/continue
            self.interruption_recovery_count += (
                1  # Assume recovery for now, Judge will verify
            )

        elif event_type == "vad_score":
            # Could be used for advanced barge-in simulation
            pass

    async def add_message(self, role: str, content: str):
        self.turn_count += 1
        self.history.append({"role": role, "content": content})

        if self.db_session:
            async with self.db_session._lock:
                msg = Message(
                    conversation_id=self.conversation_id,
                    role=role,
                    content=content,
                    turn_number=self.turn_count,
                )
                self.db_session.add(msg)
                try:
                    await self.db_session.commit()
                except Exception:
                    await self.db_session.rollback()

    async def stop(self):
        self.is_running = False
