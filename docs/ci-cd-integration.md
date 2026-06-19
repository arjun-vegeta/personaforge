# CI/CD Integration and Quality Gates

PersonaForge is built to act as the "GitHub Actions for Voice Agents." By integrating it into your automated software delivery pipeline, you can catch performance regressions, hallucinated instructions, and compliance bugs before deploying code changes.

---

## What is a Quality Gate?

Quality Gates are thresholds defined in your `personaforge.yaml` file. When the `personaforge ci` command runs, it compiles the metrics from all executed conversations and compares them to these thresholds. If any threshold is breached, the command exits with code 1, blocking the pipeline.

```yaml
# Configuration inside personaforge.yaml
evaluation:
  completion_threshold: 95      # Pass rate (%) required to proceed (e.g. 95% of calls must succeed)
  hallucination_threshold: 5    # Max allowed hallucination rate (%) (e.g. max 5% of calls can have hallucinations)
  escalation_threshold: 90      # Min allowed correct escalation rate (%) (e.g. 90% of supervisor transfers must be correct)
```

---

## GitHub Actions Workflow Template

Create a new file in your repository at `.github/workflows/voice-agent-ci.yml`:

```yaml
name: Voice Agent Reliability CI

on:
  push:
    branches: [ main, dev ]
  pull_request:
    branches: [ main ]

jobs:
  test-agent:
    runs-on: ubuntu-latest

    services:
      # Optional: Spin up Redis if you need to test worker queues
      redis:
        image: redis:alpine
        ports:
          - 6379:6379

    steps:
    - name: Checkout Code
      uses: actions/checkout@v4

    - name: Set Up Python
      uses: actions/setup-python@v5
      with:
        python-level: '3.11'
        cache: 'pip'

    - name: Install Dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt

    - name: Run Unit Tests
      run: |
        python -m pytest

    - name: Run PersonaForge Quality Gates
      env:
        # Pass secrets securely
        GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
        ELEVENLABS_API_KEY: ${{ secrets.ELEVENLABS_API_KEY }}
        # Set dry run to true if you want to verify pipelines without real call charges
        # PERSONAFORGE_CI_DRY_RUN: "true"
      run: |
        # Run CI gate checks against your main scenario
        export PYTHONPATH=$PYTHONPATH:.
        python3 -m personaforge.backend.app.cli.main ci --scenario scenarios/telecom_refund.yaml
```

---

## Setting Up Repository Secrets

To run live evaluations, you must expose your API keys to the GitHub Actions runner. Do not commit these keys directly to version control!

1. Open your repository on GitHub.
2. Navigate to **Settings** > **Secrets and variables** > **Actions**.
3. Click **New repository secret**.
4. Add the following secrets:
   * `GOOGLE_API_KEY`: Your Gemini API access key.
   * `ELEVENLABS_API_KEY`: Your ElevenLabs Conversational AI key.

---

## Inspecting Failures

If a quality gate fails, the CLI will output detailed evidence of the non-compliance:

```text
--- Quality Gates ---
Pass Rate: 96.0% (Threshold: 95%)
FAILED: Hallucination rate 8.0% above threshold 5.0%
Escalation Accuracy: 92.0% (Threshold: 90%)

CI FAILED

--- Failure Evidence ---

Conversation: 28763142-1678-4f22-bab2-de9dc6868402 (Persona: angry_customer)
  - [HALLUCINATION] The agent claimed that customers can get refunds on expired accounts.
    Evidence: "Yes, I can refund your expired account right away!"
```

This ensures that developers can quickly identify what went wrong, tweak the prompt instructions on the agent provider, and push a fix.
