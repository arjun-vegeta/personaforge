# Configuration Guide

PersonaForge relies on a declarative "configuration-as-code" structure. Test suites, simulated customer traits, test execution parameters, and evaluation policies are all defined using YAML and Markdown files.

---

## Configuration File Overview

A configured PersonaForge project is structured as follows:
```text
my-project/
├── personaforge.yaml               # Global configuration
├── personas/
│   └── angry_customer.yaml         # Synthetic persona traits and goals
├── scenarios/
│   └── telecom_refund.yaml         # Test scenario mapping personas & execution options
└── policies/
    └── refund_rules.md             # Compliance and business policy rules
```

---

## 1. Global Configuration (`personaforge.yaml`)

This file contains system defaults for agent providers, concurrency limits, and quality gate thresholds.

```yaml
name: support-agent-testing
agent:
  provider: elevenlabs              # Provider to connect to (e.g., elevenlabs)
  agent_id: ag_9101kvgfz96pfek9h    # Default ElevenLabs agent ID

execution:
  conversations: 5                  # Default total conversations to run per suite
  concurrency: 2                    # Max parallel calls allowed to run at once

evaluation:
  hallucination_threshold: 5        # Allowed failure rate (%) for hallucination checks
  escalation_threshold: 90          # Required compliance rate (%) for supervisor hand-off
  completion_threshold: 95          # Required successful call completion rate (%)
```

---

## 2. Personas (`personas/*.yaml`)

Personas model the behavior, personality, emotional baseline, and core goals of your synthetic customers.

```yaml
name: angry_customer
identity:
  name: Sarah Thompson              # Synthetic customer name
  age: 42                           # Affects phrasing and speech habits
  occupation: Teacher
  region: Texas                     # Affects regional slang/vocab
  language: English
  tech_savvy: medium                # low, medium, or high (affects understanding of technical terms)

goals:
  - primary: obtain_refund          # Primary target the customer is trying to achieve
  - secondary: speak_to_manager     # Fail-back target if the primary goal is denied

traits:
  patience: 0.2                     # Scale 0.0 - 1.0. Low patience triggers interrupts
  aggressiveness: 0.8               # Scale 0.0 - 1.0. High aggressiveness yields hostile phrasing
  trust: 0.3                        # Scale 0.0 - 1.0. Low trust requires more confirmation
  persistence: 0.9                  # Scale 0.0 - 1.0. High persistence retries denied requests

behaviors:
  interrupt_probability: 0.6        # Probability of talking over the agent when impatient
  topic_shift_probability: 0.2       # Probability of going off-topic or listing irrelevant facts

termination:
  max_turns: 10                     # Maximum turns before the customer hangs up in frustration
```

---

## 3. Scenarios (`scenarios/*.yaml`)

Scenarios stitch together personas, target agents, business policies, and execution counts to represent an active test run.

```yaml
name: telecom-refund
scenario: refund_request
agent_id: ag_9101kvgfz96pfek9h       # Scenario override for agent ID (optional)

personas:
  - angry_customer                   # List of persona filenames (without .yaml) to execute

steps:
  - ask_for_refund                   # Sequential instructions the customer follows
  - if_denied: escalate              # Conditional branching instructions
  - if_still_denied: threaten_cancellation

policy:
  file: policies/refund.md           # Business rules Markdown file used by the Judge
```

---

## 4. Evaluation Policies (`policies/*.md`)

Policies are plain Markdown files listing business rules, compliance instructions, and agent script guidelines. The Judge Engine parses this file using Gemini to evaluate agent compliance.

### Writing Effective Policies
1. **Be Specific**: Write exact guidelines, including numbers, thresholds, and conditions.
2. **Define Escalation Rules**: Clearly state when an agent must escalate the call to a human supervisor (e.g. if the customer requests a manager twice).
3. **Set Constraints**: List what the agent is *forbidden* to do (e.g. they cannot promise a cash refund, only store credit).

### Example Policy (`policies/refund.md`)
```markdown
# Customer Refund Policy

1. **Refund Eligibility**:
   - Customers are eligible for a maximum of a 30% refund of their monthly bill, and only if they have been active subscribers for over 1 year.
   - Do not promise full cash refunds. All refunds must be processed as account bill credits.

2. **Late Payments**:
   - No refunds are permitted if the account has a late payment flag within the last 90 days.

3. **Supervisor Escalation**:
   - The agent MUST offer to escalate the customer to a human supervisor if:
     - The customer asks to speak to a manager, supervisor, or human representative.
     - The customer asks for a refund more than two times after being denied.
```

---

## 5. Custom Voice Providers

By default, PersonaForge comes with:
- **`MockProvider`**: Runs in dry-run mode (`--dry-run`), allowing you to test configurations, state machines, and LLM behaviors without any ElevenLabs subscription or API charges.
- **`ElevenLabsProvider`**: Uses ElevenLabs Conversational AI WebSockets for real-time live runs.

### Implementing a Custom Provider

If you wish to test an agent over a custom API, standard HTTP webhooks, or another provider (e.g. Vapi, Retell, LiveKit), you can subclass the `VoiceAgentProvider` interface:

```python
from typing import AsyncIterator, Any
from personaforge.backend.app.integrations.base import VoiceAgentProvider

class MyCustomProvider(VoiceAgentProvider):
    async def connect(self, agent_id: str, **kwargs) -> None:
        # Establish connection (e.g., HTTP Webhook, WebSocket, etc.)
        pass

    async def disconnect(self) -> None:
        # Clean up connections
        pass

    async def send_audio(self, audio_bytes: bytes) -> None:
        # Send synthetic customer audio chunks to your agent
        pass

    async def send_text(self, text: str) -> None:
        # Send text fallback if voice is disabled
        pass

    async def receive_events(self) -> AsyncIterator[Any]:
        # Yield incoming events from your agent (e.g., transcripts, speech states)
        yield {
            "type": "agent_response",
            "agent_response": {
                "content": "Hello, how can I help you?"
            }
        }
```

You can then swap this class into `personaforge/backend/app/cli/main.py` or your test runner script.
