from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4
from sqlalchemy import Column, JSON
from sqlmodel import SQLModel, Field, Relationship


class Agent(SQLModel, table=True):
    __tablename__ = "agents"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str
    provider: str
    config: dict = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)

    conversations: List["Conversation"] = Relationship(back_populates="agent")


class Scenario(SQLModel, table=True):
    __tablename__ = "scenarios"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str
    config: dict = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)

    conversations: List["Conversation"] = Relationship(back_populates="scenario")


class TestRun(SQLModel, table=True):
    __tablename__ = "test_runs"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    scenario_name: str
    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = Field(default=None)
    total_conversations: int = Field(default=0)
    passed_conversations: int = Field(default=0)
    failed_conversations: int = Field(default=0)
    total_cost: float = Field(default=0.0)
    status: str = Field(default="pending")  # pending, active, completed, failed

    conversations: List["Conversation"] = Relationship(back_populates="test_run")


class Conversation(SQLModel, table=True):
    __tablename__ = "conversations"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    test_run_id: Optional[UUID] = Field(default=None, foreign_key="test_runs.id")
    scenario_id: Optional[UUID] = Field(default=None, foreign_key="scenarios.id")
    agent_id: Optional[UUID] = Field(default=None, foreign_key="agents.id")
    persona_id: Optional[str] = Field(default=None)  # Persona ID from YAML or DB
    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = Field(default=None)
    status: str = Field(default="pending")  # pending, active, completed, failed

    # Cost Tracking (Part 2 Requirement)
    tts_cost: float = Field(default=0.0)
    stt_cost: float = Field(default=0.0)
    llm_cost: float = Field(default=0.0)
    total_cost: float = Field(default=0.0)

    # Voice Specific Metrics (Part 5 Requirement)
    interruption_count: int = Field(default=0)
    interruption_recovery_count: int = Field(default=0)
    avg_latency: float = Field(default=0.0)
    accent: Optional[str] = Field(default=None)

    # Recovery and Error Info
    error_message: Optional[str] = None
    retry_count: int = Field(default=0)

    test_run: Optional[TestRun] = Relationship(back_populates="conversations")
    agent: Optional[Agent] = Relationship(back_populates="conversations")
    scenario: Optional[Scenario] = Relationship(back_populates="conversations")
    messages: List["Message"] = Relationship(back_populates="conversation")
    evaluations: List["Evaluation"] = Relationship(back_populates="conversation")


class Message(SQLModel, table=True):
    __tablename__ = "messages"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    conversation_id: UUID = Field(foreign_key="conversations.id")
    role: str  # agent, customer, system
    content: str
    turn_number: int
    created_at: datetime = Field(default_factory=datetime.utcnow)

    conversation: Conversation = Relationship(back_populates="messages")


class Evaluation(SQLModel, table=True):
    __tablename__ = "evaluations"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    conversation_id: UUID = Field(foreign_key="conversations.id")
    result: dict = Field(default_factory=dict, sa_column=Column(JSON))

    # Failure Metrics (Part 2 Requirement)
    hallucination_detected: bool = Field(default=False)
    escalation_failure: bool = Field(default=False)
    completion_failure: bool = Field(default=False)

    # Voice Specific Metrics (Part 5 Requirement)
    interruption_recovery_rate: float = Field(default=0.0)
    accent_robustness_score: float = Field(default=0.0)

    severity: str = Field(default="low")  # low, medium, high, critical

    created_at: datetime = Field(default_factory=datetime.utcnow)

    conversation: Conversation = Relationship(back_populates="evaluations")
