# CreatorRadar — Development Rules

## Python standards

- Type hints required on all function signatures
- Docstrings required on functions with non-obvious behavior or side effects
- `black` formatter enforced (line length: 88)
- No unused imports
- Environment variables loaded via `python-dotenv`, never hardcoded
- All file paths constructed with `pathlib.Path`, not string concatenation

```python
# correct
def upload_json(data: list[dict], gcs_path: str) -> None:
    """Upload a list of dicts as JSON to the given GCS path."""
    ...

# incorrect
def upload(d, path):
    ...
```

## dbt standards

- Model names: `stg_` prefix for staging, `int_` for intermediate, `mart_` for marts
- All models have a description in `schema.yml`
- `not_null` and `unique` tests on all primary keys
- `accepted_values` tests on categorical columns (topic, signal flags)
- No raw table references in intermediate or mart models — always reference staging
- Macros documented with a comment block explaining inputs and output

## Git

- Commit directly to `main`
- Commit messages: `type: short description` format
  - `feat: add sponsor signal macro`
  - `fix: handle null duration in staging`
  - `chore: update tracking config with new brands`
  - `docs: update architecture with brand mentions mart`
- One logical change per commit — do not bundle unrelated changes

## File and folder rules

- Ingestion scripts live in `ingestion/` — no business logic, only API calls and uploads
- Business logic (scoring, signal detection) lives in dbt macros and models
- Config changes (new keywords, new brands, new creators) go in `data/tracking_config.yaml` only
- No hardcoded keyword lists in Python — always read from config
- Raw data is never modified after write — append only

## Environment

- `.env` is never committed (in `.gitignore`)
- `.env.example` is always kept up to date
- New environment variables must be added to `.env.example` with a placeholder value and a comment explaining what it is

---

## Agent system

Agents are specialized assistants that activate based on the current task. Only the relevant agent is loaded per session to minimize context and token usage.

**Always loaded (every session):**
- `PROJECT.md`
- `ARCHITECTURE.md`
- `RULES.md`

**Loaded on demand (one per session):**
The active agent's log file is loaded when the session task matches the agent's domain.

### Cross-agent protocol

During any session, if a decision or change affects a domain outside the active agent's scope, the assistant will proactively flag it:

```
⚠️  This affects [Agent Name]. Should we activate it now or note it for the next session?
```

At session end, the active agent writes a brief handoff note to any other agent log files that were touched during the session. The note contains only what the next agent needs to know to pick up — not a full log. Detailed logging happens when that agent's own session begins.

**Single-operator rule:** This is a single-person project. There is no separate Orchestrator session. The active agent handles cross-agent handoff notes directly at session end.

---

## Agents

### Deployment Agent
**File:** `agents/deployment_agent.md`

**Activates when:** Setting up GCP infrastructure, configuring Airflow, building Docker images, updating environment variables, or running `docker compose` commands.

**Responsibilities:**
- Guide GCP project setup (BigQuery dataset, GCS bucket, service account, IAM roles)
- Guide Airflow Docker build and startup sequence
- Validate that `.env` variables are correctly set
- Track which infrastructure components are live vs pending

**Log format:** Date, action taken, current infrastructure state, next step.

---

### Ingestion Agent
**File:** `agents/ingestion_agent.md`

**Activates when:** Writing or modifying `ingestion/` scripts, debugging YouTube API calls, managing quota, checking GCS upload status, or loading data to BigQuery.

**Responsibilities:**
- Track daily quota usage against the 10,000 unit budget
- Monitor which days have complete vs missing raw data in GCS
- Guide debugging of failed API calls or GCS upload errors
- Confirm raw table row counts after BQ load

**Log format:** Date, videos fetched, channels fetched, quota used, GCS files written, BQ rows loaded, errors.

---

### dbt Agent
**File:** `agents/dbt_agent.md`

**Activates when:** Writing or modifying dbt models, macros, or tests; running `dbt run` or `dbt test`; debugging failed model builds or test failures.

**Responsibilities:**
- Track which models exist and their last successful run
- Surface test failures with plain-language explanations
- Guide fixes for failed models
- Keep `schema.yml` in sync with model changes

**Log format:** Date, models run, tests passed, tests failed (with reason), next action.

---

### Data Quality Agent
**File:** `agents/data_quality_agent.md`

**Activates when:** Investigating anomalies in BigQuery tables, checking row counts, validating score distributions, or reviewing dbt test output.

**Responsibilities:**
- Flag days where row counts are significantly below average
- Check that `commercial_fit_score` distribution is non-trivial (not all scores clustered)
- Verify sponsor signal and commerce intent detection is firing at expected rates
- Alert if a category disappears from mart tables

**Log format:** Date, tables checked, anomalies found, action taken.

---

### Frontend Agent
**File:** `agents/frontend_agent.md`

**Activates when:** Writing React components, debugging FastAPI-to-frontend connection, building or deploying the frontend.

**Responsibilities:**
- Verify FastAPI endpoints return data the frontend expects
- Guide component build and local dev server setup
- Track which pages are built vs in progress
- Guide deployment when ready

**Log format:** Date, components built, API endpoints connected, issues found, next step.

---

### Orchestrator Agent
**File:** `agents/orchestrator_agent.md`

**Activates:** At the end of sessions where cross-agent updates occurred, or when the task involves coordinating multiple domains at once.

**Responsibilities:**
- Review session output for decisions that affect other agents
- Prompt updates to relevant agent log files
- Does not activate mid-session unless explicitly called — this keeps token cost low

**Log format:** Date, session summary, cross-agent updates applied, agent files modified.
