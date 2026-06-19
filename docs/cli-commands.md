# CLI Command Reference

The PersonaForge Command Line Interface (CLI) is the primary developer tool for orchestrating voice agent reliability testing. Ensure you set your Python environment path before running commands:

```bash
export PYTHONPATH=$PYTHONPATH:.
```

---

## Project Scaffolding Commands

### `init`
Initializes a new PersonaForge project in the current directory, scaffolding default configuration directories, sample YAMLs, and policies.
* **Usage**:
  ```bash
  python3 -m personaforge.backend.app.cli.main init
  ```

### `persona create <name>`
Creates a pre-populated synthetic customer persona template file under `personas/<name>.yaml`.
* **Usage**:
  ```bash
  python3 -m personaforge.backend.app.cli.main persona create confused_senior
  ```

### `scenario create <name>`
Creates a pre-populated test scenario template file under `scenarios/<name>.yaml`.
* **Usage**:
  ```bash
  python3 -m personaforge.backend.app.cli.main scenario create billing_dispute
  ```

---

## Test Execution Commands

### `run <scenario_file>`
Executes the specified testing scenario using concurrent synthetic customer agents.

```bash
python3 -m personaforge.backend.app.cli.main run <scenario_file> [options]
```

#### Options:
* `--persona <name>`: Override and run only a specific persona file (can be passed multiple times).
* `--concurrency <integer>`: Maximum number of calls to execute in parallel.
* `--count <integer>`: Total number of conversations to run in the test suite.
* `--dry-run`: Runs the suite with simulated network calls and mocks (ideal for testing configuration and code changes without incurring voice generation fees).

#### Example:
```bash
# Run 10 conversations with a concurrency limit of 3 in dry-run mode
python3 -m personaforge.backend.app.cli.main run scenarios/telecom_refund.yaml --count 10 --concurrency 3 --dry-run
```

---

## Reporting and Inspection Commands

### `report [report_file]`
Displays a formatted dashboard summary of the specified run report directly in the terminal.
* **Usage**:
  ```bash
  # View summary of the most recent run
  python3 -m personaforge.backend.app.cli.main report latest

  # View summary of a specific report file
  python3 -m personaforge.backend.app.cli.main report reports/report_20260619_232836.json
  ```

### `replay <conversation_id>`
Prints the turn-by-turn text transcript of a finished conversation call.
* **Usage**:
  ```bash
  python3 -m personaforge.backend.app.cli.main replay 28763142-1678-4f22-bab2-de9dc6868402
  ```

### `compare <report_base> <report_current>`
Analyzes two report run files to identify performance deviations or new failure categories.
* **Usage**:
  ```bash
  python3 -m personaforge.backend.app.cli.main compare report_20260618_024753 report_20260619_232836
  ```

---

## CI/CD and Production Integration Commands

### `ci`
Executes test runs optimized for automated pipeline quality gates.
* **Usage**:
  ```bash
  python3 -m personaforge.backend.app.cli.main ci --scenario scenarios/telecom_refund.yaml
  ```
* **Exit Codes**:
  * `0`: Test suite passed all quality gates specified in `personaforge.yaml`.
  * `1`: Test suite failed one or more quality gates (or hit a runtime error). Logs failure evidence detailing the specific conversation and failure reasons.
* **CI Dry Run Environment Variable**:
  Set `PERSONAFORGE_CI_DRY_RUN=true` to validate pipelines using mock providers:
  ```bash
  PERSONAFORGE_CI_DRY_RUN=true python3 -m personaforge.backend.app.cli.main ci --scenario scenarios/telecom_refund.yaml
  ```

### `worker`
Starts a background Redis Queue (RQ) task worker to asynchronously pull tasks off of queues.
* **Usage**:
  ```bash
  # Listen to all queues (conversation, evaluation, report)
  python3 -m personaforge.backend.app.cli.main worker

  # Listen to a specific queue
  python3 -m personaforge.backend.app.cli.main worker --queue evaluation
  ```
