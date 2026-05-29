import pytest
from sqlmodel import Session, SQLModel, create_engine, select
from personaforge.backend.app.database.models import Agent, Scenario, Conversation, Message, Evaluation, TestRun

@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

def test_create_test_run(session: Session):
    test_run = TestRun(
        scenario_name="telecom-refund",
        total_conversations=10,
        passed_conversations=8,
        failed_conversations=2,
        total_cost=0.15,
        status="completed"
    )
    session.add(test_run)
    session.commit()
    session.refresh(test_run)
    
    assert test_run.id is not None
    assert test_run.scenario_name == "telecom-refund"
    assert test_run.status == "completed"

def test_test_run_conversations(session: Session):
    test_run = TestRun(scenario_name="test")
    session.add(test_run)
    session.commit()
    
    conv = Conversation(test_run_id=test_run.id, status="completed")
    session.add(conv)
    session.commit()
    session.refresh(test_run)
    
    assert len(test_run.conversations) == 1
    assert test_run.conversations[0].test_run_id == test_run.id

def test_create_agent(session: Session):
    agent = Agent(name="Test Agent", provider="elevenlabs", config={"agent_id": "123"})
    session.add(agent)
    session.commit()
    session.refresh(agent)
    
    assert agent.id is not None
    assert agent.name == "Test Agent"
    assert agent.config["agent_id"] == "123"

def test_create_conversation_with_relationships(session: Session):
    agent = Agent(name="Agent", provider="test")
    scenario = Scenario(name="Scenario", config={})
    session.add(agent)
    session.add(scenario)
    session.commit()
    
    conv = Conversation(agent_id=agent.id, scenario_id=scenario.id, status="active")
    session.add(conv)
    session.commit()
    session.refresh(conv)
    
    assert conv.agent.name == "Agent"
    assert conv.scenario.name == "Scenario"

def test_conversation_messages(session: Session):
    conv = Conversation(status="active")
    session.add(conv)
    session.commit()
    
    msg1 = Message(conversation_id=conv.id, role="agent", content="Hello", turn_number=1)
    msg2 = Message(conversation_id=conv.id, role="customer", content="Hi", turn_number=2)
    session.add(msg1)
    session.add(msg2)
    session.commit()
    session.refresh(conv)
    
    assert len(conv.messages) == 2
    assert conv.messages[0].content == "Hello"

def test_conversation_evaluations(session: Session):
    conv = Conversation(status="completed")
    session.add(conv)
    session.commit()
    
    eval = Evaluation(
        conversation_id=conv.id, 
        result={"pass": True},
        hallucination_detected=False,
        severity="low"
    )
    session.add(eval)
    session.commit()
    session.refresh(conv)
    
    assert len(conv.evaluations) == 1
    assert conv.evaluations[0].severity == "low"
    assert conv.evaluations[0].hallucination_detected is False
