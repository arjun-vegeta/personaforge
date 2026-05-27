from redis import Redis
from rq import Queue
import os

class QueueManager:
    def __init__(self, redis_url=None):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self.redis = Redis.from_url(self.redis_url)
        self.conversation_queue = Queue("conversation_queue", connection=self.redis)
        self.evaluation_queue = Queue("evaluation_queue", connection=self.redis)
        self.report_queue = Queue("report_queue", connection=self.redis)

    def enqueue_conversation(self, scenario_config, persona_name, agent_id, dry_run=False):
        return self.conversation_queue.enqueue(
            "personaforge.backend.app.runner.workers.run_conversation_task",
            scenario_config=scenario_config,
            persona_name=persona_name,
            agent_id=agent_id,
            dry_run=dry_run
        )

    def enqueue_evaluation(self, conversation_id, history, policy_doc, scenario_config):
        return self.evaluation_queue.enqueue(
            "personaforge.backend.app.runner.workers.run_evaluation_task",
            conversation_id=conversation_id,
            history=history,
            policy_doc=policy_doc,
            scenario_config=scenario_config
        )

    def enqueue_report(self, run_results, report_id):
        return self.report_queue.enqueue(
            "personaforge.backend.app.runner.workers.run_report_task",
            run_results=run_results,
            report_id=report_id
        )
