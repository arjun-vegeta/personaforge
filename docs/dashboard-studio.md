# PersonaForge Studio (Dashboard)

PersonaForge Studio is the web-based visual dashboard for inspecting test executions, browsing conversation replays, analyzing voice metrics (like latency and interruptions), and investigating compliance failures.

---

## How to Run the Dashboard

The dashboard consists of a FastAPI backend server and a Next.js web application.

### Step 1: Start the Backend API
From the root directory of the project, activate your virtual environment and start the FastAPI server:
```bash
# Activate virtualenv if not already active
source venv/bin/activate

# Launch the FastAPI app on port 8000
uvicorn personaforge.backend.app.main:app --reload
```
The API documentation will be available at `http://localhost:8000/docs`.

### Step 2: Start the Web Frontend
Open a new terminal window, navigate to the web directory, install dependencies, and start the development server:
```bash
cd personaforge/web

# Install packages (first-time only)
npm install

# Start the dev server on port 3000
npm run dev
```
Open your browser and navigate to `http://localhost:3000`.

---

## Dashboard Interface Walkthrough

### 1. Main Overview and Statistics
At the top of the Studio landing page, you will find summary cards capturing global test statistics:
* **Pass Rate**: The percentage of test conversations that fully met your scenario conditions and policy compliance rules.
* **Total Conversations**: The cumulative count of simulated customer sessions run.
* **Total Cost**: Integrated calculation tracking TTS (text-to-speech), STT (speech-to-text), and LLM reasoning fees.
* **Average Latency**: The average time it took the voice agent to respond.
* **Interruption Recovery**: The success rate of the agent returning to its core script after a customer interrupts them mid-sentence.

### 2. Test Runs History
The main table displays historical runs grouped by date and scenario name.
* Each entry displays the status (`completed`, `active`, or `failed`), run durations, pass rates, and cost.
* Click on any Test Run to expand the detailed list of conversations executed during that run.

### 3. Conversation Replay and Failure Logs
Selecting an individual conversation opens the deep-dive panel:
* **Chat Transcript**: A clean, chronological timeline showing dialog turns between the synthetic customer and your voice agent.
* **Compliance Checks**: Details of the evaluation engine's checks (e.g., whether the agent hallucinated policies, failed to escalate, or deviated from instructions).
* **Failure Evidence**: If a check fails, the interface highlights the exact turn of dialogue that triggered the non-compliance along with a reasoning snippet from the Judge engine.

---

## Storage and Database Details

PersonaForge saves all data (test runs, conversation transcripts, turn-by-turn messages, and evaluation results) in a database.
* By default, it reads and writes to a local SQLite database file named `personaforge.db` in the project root.
* You can switch to a production PostgreSQL database by altering the `DATABASE_URL` parameter in your `.env` file.
* Because the runner executes multiple conversations concurrently, the system automatically handles database access using a thread-safe connection pool with write locks to prevent SQLite locking issues.
