import asyncio
from typing import List
from personaforge.backend.app.runner.runner import ConversationRunner


class TestOrchestrator:
    def __init__(self, concurrency: int = 10):
        self.concurrency = concurrency
        self.semaphore = asyncio.Semaphore(concurrency)

    async def run_suite(self, runners: List[ConversationRunner]):
        tasks = []
        for runner in runners:
            tasks.append(self._run_with_semaphore(runner))

        await asyncio.gather(*tasks)

    async def _run_with_semaphore(self, runner: ConversationRunner):
        async with self.semaphore:
            await runner.run()
