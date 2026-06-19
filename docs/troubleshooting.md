# Troubleshooting Guide

Here is a list of common issues, error codes, and practical steps to resolve them when using PersonaForge.

---

## 1. SQLite Database is Locked (`OperationalError: database is locked`)

### The Problem
During high-concurrency test runs (e.g. `--concurrency 10`), multiple threads or async tasks attempt to write metrics, transcripts, and evaluation results to the SQLite file simultaneously. Since SQLite only supports one active writer, this triggers write locks.

### The Solution
1. **Built-in Session Locking**: The PersonaForge codebase includes an `asyncio.Lock` wrapper around session adds and commits in the conversation runner. Ensure you are importing and utilizing the database sessions through the provided orchestrator framework.
2. **Switch to PostgreSQL**: For large-scale production test suites or high concurrency, swap SQLite for PostgreSQL by updating the `DATABASE_URL` in your `.env` file:
   ```env
   DATABASE_URL=postgresql+asyncpg://user:password@localhost:5412/personaforge
   ```

---

## 2. ElevenLabs WebSocket Errors (Connection Code `3001` / `internal_error`)

### The Problem
When launching a live scenario run, the connection immediately drops with a WebSocket close code `3001` or general `internal_error`.

### The Solution
1. **Invalid Voice ID**: ElevenLabs conversational agents require a valid voice ID. Some default voice IDs (like Rachel: `21m00Tcm4TlvDq8ikWAM`) may be disabled or restricted in newer account formats. 
   - Open your ElevenLabs Conversational AI Agent dashboard.
   - Assign a widely available default voice, such as **Sarah** (`EXAVITQu4vr4xnSDxMaL`) or **George** (`JBFqnCBsd6RMkjVDRZzb`).
2. **Account Tier Constraints**: Free tier ElevenLabs accounts may restrict real-time WebSocket conversational audio streams. Ensure you have linked a payment method or have active credits on your ElevenLabs account.
3. **Check API Credentials**: Verify that `ELEVENLABS_API_KEY` is set correctly in your `.env` file and that the agent ID specified in `personaforge.yaml` matches the agent owned by that API key.

---

## 3. Google Gemini Rate Limits (TPM / RPM Errors)

### The Problem
During large evaluations (e.g. evaluating 50 conversations at once), the Judge or Persona Engine throws a 429 Rate Limit error from Google AI Studio.

### The Solution
1. **Built-in Retry Mechanism**: The PersonaForge backend includes a built-in exponential backoff retry handler (`_call_with_retry`) in the `LLMClient`. On receiving a `429 RESOURCE_EXHAUSTED` error, the client automatically pauses and retries (up to 5 attempts, doubling the wait time on each attempt).
2. **Reduce Concurrency**: Lower the concurrency rate in your run command:
   ```bash
   python3 -m personaforge.backend.app.cli.main run scenarios/telecom_refund.yaml --concurrency 2
   ```
3. **Use Batch Tasks**: Offload evaluations to the background task queue worker using Redis:
   ```bash
   python3 -m personaforge.backend.app.cli.main worker --queue evaluation
   ```
4. **Upgrade Tier**: Shift from the free Gemini Tier to a pay-as-you-go billing plan in Google AI Studio to increase your Requests Per Minute (RPM) limits.

---

## 4. Web Dashboard (Studio) Shows No Data / Empty Screen

### The Problem
You spin up the Next.js frontend, but the run logs and statistics charts are completely empty.

### The Solution
1. **Verify Database Location**: Ensure the FastAPI backend is reading the same `personaforge.db` file that the CLI wrote to. Make sure both process environments share the exact same `.env` values and work directories.
2. **Initialize Database Tables**: Check if database migrations have run. The CLI automatically runs migrations on startup, but you can force-verify by running:
   ```bash
   PYTHONPATH=. python3 -m personaforge.backend.app.cli.main run scenarios/telecom_refund.yaml --count 1 --dry-run
   ```
3. **Re-run Simulation**: Old test runs might not have persisted correctly. Run a fresh dry-run simulation using the current codebase to populate the SQLite tables:
   ```bash
   PYTHONPATH=. python3 -m personaforge.backend.app.cli.main run scenarios/telecom_refund.yaml --count 5 --dry-run
   ```
