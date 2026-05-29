# PersonaForge

> **"How do we know our voice agent won't fail in production?"**
>
> PersonaForge answers that question before your first customer call.

PersonaForge is a synthetic customer generation and reliability testing platform for conversational voice agents. It acts as the "GitHub Actions for Voice Agents," allowing developers to autonomously validate behavior, reliability, and compliance through thousands of simulated customer interactions.

---

## The Vision

Traditional testing for voice agents is broken. It's manual, slow, and ignores voice-native failures like interruptions and latency.

**The PersonaForge Way:**
```text
Build Agent -> 1,000 Synthetic Customers -> Failure Detection -> Deploy Safely
```

## Key Features

- **Forge (Persona Engine):** Goal-driven, emotionally consistent synthetic customers. They don't just generate text; they maintain memory, pursue subgoals, and react to agent behavior.
- **Runner (Execution Engine):** High-concurrency voice-native conversation runner. Supports ElevenLabs Conversational AI with real-time audio streaming.
- **Judge (Evaluation Engine):** Multi-stage LLM evaluation that detects:
  - **Hallucinations:** Agent inventing policies or facts.
  - **Escalation Failures:** Agent failing to hand off to a human when required.
  - **Compliance:** Violations of safety or business rules.
  - **Voice Metrics:** Interruption recovery and response latency.
- **CI/CD Integration:** Built-in quality gates for your deployment pipeline.
- **Studio (Dashboard):** Visualize regressions, explore failure clusters, and replay conversations turn-by-turn.

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/personaforge.git
cd personaforge

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure API Keys

Create a .env file in the root directory:

```env
ELEVENLABS_API_KEY=your_key_here
GOOGLE_API_KEY=your_gemini_key_here
```

### 3. Initialize Project

```bash
export PYTHONPATH=$PYTHONPATH:.
python3 -m personaforge.backend.app.cli.main init
```

### 4. Run a Scenario

```bash
python3 -m personaforge.backend.app.cli.main run scenarios/telecom_refund.yaml
```

### 5. Check for Regressions (CI Mode)

```bash
python3 -m personaforge.backend.app.cli.main ci --scenario scenarios/telecom_refund.yaml
```

## Dashboard

The PersonaForge Studio provides a deep dive into your agent's health.

```bash
# Start the backend
uvicorn personaforge.backend.app.main:app --reload

# Start the frontend
cd personaforge/web
npm install
npm run dev
```

Visit `http://localhost:3000` to view pass rates, failure clusters, and conversation replays.

## Docker Support

You can run the entire PersonaForge stack (PostgreSQL, Redis, Backend, Frontend, and Worker) using Docker Compose:

```bash
# Create a .env file with your API keys
cp .env.example .env

# Start the services
docker-compose up --build
```

## CI/CD Integration

PersonaForge is designed to be part of your development workflow. The repository includes a GitHub Action template in .github/workflows/ci.yml that:
1. Runs unit tests.
2. Initializes the PersonaForge environment.
3. Executes a CI quality gate check against your scenarios.

To use this, add GOOGLE_API_KEY and ELEVENLABS_API_KEY to your GitHub repository secrets.

## Architecture

PersonaForge is built with a modular, provider-first architecture:
- **FastAPI / SQLModel:** High-performance backend with PostgreSQL.
- **Gemini 3.1 Flash Lite:** Ultra-low latency LLM reasoning for customer actions and judging.
- **ElevenLabs ConvAI:** Direct WebSocket integration for voice interaction.
- **Redis / RQ:** Asynchronous task processing for large-scale test suites.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

Built for the future of Conversational AI.
