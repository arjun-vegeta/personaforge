from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import select, func, desc
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime, timedelta

from personaforge.backend.app.database.connection import get_session, init_db
from personaforge.backend.app.database.models import TestRun, Conversation, Message, Evaluation

app = FastAPI(title="PersonaForge API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def on_startup():
    await init_db()

@app.get("/api/runs")
async def get_runs(session: AsyncSession = Depends(get_session)):
    statement = select(TestRun).order_by(desc(TestRun.started_at))
    results = await session.execute(statement)
    runs = results.scalars().all()
    
    # Map to frontend expected format
    return [
        {
            "id": str(run.id),
            "timestamp": run.started_at.isoformat(),
            "status": run.status,
            "pass_rate": (run.passed_conversations / run.total_conversations * 100) if run.total_conversations > 0 else 0,
            "total_conversations": run.total_conversations,
            "total_failures": run.failed_conversations,
            "cost": run.total_cost,
            "version": "v1.0.0" # Placeholder for versioning
        }
        for run in runs
    ]

@app.get("/api/runs/{run_id}")
async def get_run_details(run_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    run = await session.get(TestRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    statement = select(Conversation).where(Conversation.test_run_id == run_id)
    results = await session.execute(statement)
    conversations = results.scalars().all()
    
    # Enrich conversations with evaluation status
    enriched_conversations = []
    for conv in conversations:
        eval_statement = select(Evaluation).where(Evaluation.conversation_id == conv.id)
        eval_result = await session.execute(eval_statement)
        evaluation = eval_result.scalar_one_or_none()
        
        enriched_conversations.append({
            "id": str(conv.id),
            "persona_id": conv.persona_id,
            "status": "passed" if evaluation and evaluation.result.get("pass_status", False) else "failed",
            "total_cost": conv.total_cost,
            "passed": evaluation.result.get("pass_status", False) if evaluation else False,
            "failures": evaluation.result.get("failures", []) if evaluation else []
        })
    
    return {
        "run": {
            "id": str(run.id),
            "timestamp": run.started_at.isoformat(),
            "status": run.status,
            "pass_rate": (run.passed_conversations / run.total_conversations * 100) if run.total_conversations > 0 else 0,
            "total_conversations": run.total_conversations,
            "total_failures": run.failed_conversations,
            "cost": run.total_cost
        },
        "conversations": enriched_conversations
    }

@app.get("/api/conversations/{conversation_id}")
async def get_conversation(conversation_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    conv = await session.get(Conversation, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    msg_statement = select(Message).where(Message.conversation_id == conversation_id).order_by(Message.turn_number)
    msg_results = await session.execute(msg_statement)
    messages = msg_results.scalars().all()
    
    eval_statement = select(Evaluation).where(Evaluation.conversation_id == conversation_id)
    eval_results = await session.execute(eval_statement)
    evaluation = eval_results.scalar_one_or_none()
    
    return {
        "id": str(conv.id),
        "run_id": str(conv.test_run_id),
        "persona_name": conv.persona_id,
        "status": "passed" if evaluation and evaluation.result.get("pass_status", False) else "failed",
        "cost": conv.total_cost,
        "latency": 1.2, # Placeholder for average latency
        "turns": [
            {
                "role": "customer" if msg.role == "customer" else "agent",
                "content": msg.content,
                "timestamp": msg.created_at.isoformat()
            }
            for msg in messages
        ],
        "evaluation": evaluation.result if evaluation else None
    }

@app.get("/api/stats")
async def get_global_stats(session: AsyncSession = Depends(get_session)):
    # Global Overview Stats
    total_runs_statement = select(func.count(TestRun.id))
    total_runs = (await session.execute(total_runs_statement)).scalar()
    
    total_convs_statement = select(func.count(Conversation.id))
    total_convs = (await session.execute(total_convs_statement)).scalar()
    
    total_cost_statement = select(func.sum(TestRun.total_cost))
    total_cost = (await session.execute(total_cost_statement)).scalar() or 0.0
    
    passed_convs_statement = select(func.sum(TestRun.passed_conversations))
    passed_convs = (await session.execute(passed_convs_statement)).scalar() or 0
    
    pass_rate = (passed_convs / total_convs * 100) if total_convs > 0 else 0
    
    # Recent runs for chart (Pass rate over time)
    recent_runs_statement = select(TestRun).order_by(TestRun.started_at.asc()).limit(30)
    recent_runs = (await session.execute(recent_runs_statement)).scalars().all()
    
    pass_rate_over_time = [
        {
            "date": run.started_at.strftime("%Y-%m-%d"),
            "rate": (run.passed_conversations / run.total_conversations * 100) if run.total_conversations > 0 else 0
        }
        for run in recent_runs
    ]
    
    # Count failures by category
    failures_statement = select(Evaluation.result)
    evaluations = (await session.execute(failures_statement)).scalars().all()
    
    total_failures = 0
    for evaluation in evaluations:
        total_failures += len(evaluation.get("failures", []))

    return {
        "total_runs": total_runs,
        "total_conversations": total_convs,
        "total_failures": total_failures,
        "pass_rate": round(pass_rate, 1),
        "total_cost": round(total_cost, 2),
        "pass_rate_over_time": pass_rate_over_time
    }

@app.get("/api/agent-health")
async def get_agent_health(session: AsyncSession = Depends(get_session)):
    # Group by scenario/agent to show health trends
    statement = select(TestRun).order_by(desc(TestRun.started_at)).limit(10)
    results = await session.execute(statement)
    runs = results.scalars().all()
    
    health_metrics = []
    for i, run in enumerate(reversed(runs)):
        # Calculate rates for this run
        total = run.total_conversations
        pass_rate = (run.passed_conversations / total * 100) if total > 0 else 0
        
        # Aggregate failures from this run
        eval_statement = select(Evaluation).join(Conversation).where(Conversation.test_run_id == run.id)
        eval_results = await session.execute(eval_statement)
        evals = eval_results.scalars().all()
        
        hallucination_count = sum(1 for e in evals if e.hallucination_detected)
        escalation_failure_count = sum(1 for e in evals if e.escalation_failure)
        
        hallucination_rate = (hallucination_count / total * 100) if total > 0 else 0
        escalation_rate = ((total - escalation_failure_count) / total * 100) if total > 0 else 100
        
        # Avg Latency for the run
        avg_latency = run.total_cost / total if total > 0 else 0 # This is a placeholder for cost, let's use actual latency if we have it aggregated
        # Better: calculate from conversations
        latency_statement = select(func.avg(Conversation.avg_latency)).where(Conversation.test_run_id == run.id)
        avg_latency = (await session.execute(latency_statement)).scalar() or 0.0

        health_metrics.append({
            "version": f"v1.0.{i}",
            "completion_rate": pass_rate,
            "hallucination_rate": hallucination_rate,
            "escalation_rate": escalation_rate,
            "avg_latency": float(avg_latency)
        })
    
    return health_metrics

@app.get("/api/persona-performance")
async def get_persona_performance(session: AsyncSession = Depends(get_session)):
    # Group performance by persona_id
    statement = select(
        Conversation.persona_id,
        func.count(Conversation.id).label("total"),
        func.avg(Conversation.avg_latency).label("latency")
    ).group_by(Conversation.persona_id)
    
    results = (await session.execute(statement)).all()
    
    performance = []
    for row in results:
        # Calculate pass rate for this persona
        eval_statement = select(func.count(Evaluation.id)).join(Conversation).where(
            Conversation.persona_id == row.persona_id,
            Evaluation.severity == "low" # Simplified: "low" severity means it passed
        )
        passed_count = (await session.execute(eval_statement)).scalar() or 0
        
        pass_rate = (passed_count / row.total * 100) if row.total > 0 else 0
            
        performance.append({
            "name": row.persona_id or "Unknown",
            "pass_rate": pass_rate,
            "total_runs": row.total,
            "avg_latency": float(row.latency or 0.0)
        })
        
    return performance

@app.get("/api/failures")
async def get_failures(category: Optional[str] = None, session: AsyncSession = Depends(get_session)):
    statement = select(Evaluation).order_by(desc(Evaluation.created_at))
    if category and category != "all":
        # Filter logic in result JSONB might be complex, simplified for POC
        pass
        
    results = await session.execute(statement)
    evaluations = results.scalars().all()
    
    failures = []
    for eval in evaluations:
        # Each evaluation can have multiple failures in the 'failures' list within 'result'
        eval_failures = eval.result.get("failures", [])
        for f in eval_failures:
            if category and category != "all" and f.get("category", "").lower() != category.lower():
                continue
                
            # Get conversation/persona info
            conv = await session.get(Conversation, eval.conversation_id)
            
            failures.append({
                "id": str(eval.conversation_id),
                "type": f.get("category", "Unknown"),
                "severity": f.get("severity", "medium"),
                "persona": conv.persona_id if conv else "Unknown",
                "scenario": "Test Case",
                "evidence": f.get("reason", f.get("evidence", "No evidence")),
                "timestamp": eval.created_at.isoformat()
            })
            
    return failures

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
