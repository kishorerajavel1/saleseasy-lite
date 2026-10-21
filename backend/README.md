# SalesEasy Lite backend

FastAPI with switchable Groq/Gemini adapters through LangChain, strict structured output, grounded evidence and application-owned triage policy. Application modules live directly in this directory.

## Setup

Use Python 3.11+:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt -c requirements.lock.txt
```

Copy `.env.example` to `.env` only if the local file does not already exist. Configure the key for the selected provider. Preserve existing secrets. The project setup script handles installation and safe environment-file creation.

```dotenv
LLM_PROVIDER=groq
GROQ_API_KEY=your-key-here
GROQ_MODEL=openai/gpt-oss-20b
```

`LLM_PROVIDER` accepts `groq` or `gemini`. Only the selected provider's nonblank key is required; unsupported providers fail startup. Invalid credentials, unavailable models and quotas are reported when an analysis is requested; `/health` and its browser-facing `/status` alias do not call the provider.

## Run

```bash
./scripts/run.sh
```

For development reload:

```bash
.venv/bin/python -m uvicorn main:create_app --factory --reload --host 127.0.0.1 --port 8000 --no-proxy-headers
```

Open [API documentation](http://127.0.0.1:8000/docs). The frontend runs separately. `ALLOWED_ORIGINS` is a JSON list of frontend origins.

## Request flow

`main.py` uses the provider factory to construct the selected adapter and the analysis service. Controllers delegate to the service, which enforces a 45-second total budget, 20-second attempt timeout, bounded concurrency and at most two calls. Transient 429/5xx/network failures and deadlines are retried once; invalid structured output receives one repair attempt. Valid interpretation flows through evidence verification and deterministic safety/business policy before final validation.

The API returns explicit errors on provider failure: 502 for blocked/invalid output or rejected configuration, 503 for transient unavailability after retry, and 504 for exhausted deadlines. It does not generate a replacement analysis. Logs contain only safe metadata.

| Directory | Responsibility |
|---|---|
| `controllers/` | Routes, dependencies and safe error mapping |
| `services/` | Orchestration, grounding, policy and entity resolution |
| `schemas/` | Public API and private provider contracts |
| `repositories/` | Immutable fictional inventory |
| `domain/` | Normalization and supplementary safety checks |
| `llm/` | Provider adapters, selection factory and prompts |
| `core/`, `middleware/` | Settings, logs, body/rate limits and headers |
| `tests/` | Isolated regressions, including controlled network failures |
| `evaluation/` | Real-provider scenario runner and reports |

## Validate

```bash
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/python -m pytest -q
```

These tests do not call external providers. Network substitutes live exclusively in tests.

Run live evaluation explicitly:

```bash
.venv/bin/python -m evaluation.run --repeat 3 --delay 15
```

Reports are written to provider-named files such as `evaluation/results/groq-results.json` and `groq-results.md`. Every case uses the selected real model; errors are recorded as failures.

The report includes eight live cases plus a controlled provider-failure case. The latter injects a transient provider exception at the adapter boundary and verifies the production service returns HTTP 503 after exactly two attempts.

## Deploy

The repository-root `render.yaml` configures a one-worker Render service. It binds to Render's `$PORT`, enables proxy headers, checks `/health`, and prompts for the secret provider key and frontend origin allowlist. Set `ALLOWED_ORIGINS` as JSON, for example `["https://your-site.netlify.app"]`.

The local `scripts/run.sh` remains safe by default: it binds to `127.0.0.1` and ignores forwarded headers. Hosting can set `HOST`, `PORT`, and `FORWARDED_ALLOW_IPS` explicitly.

See the [project README](../README.md) for the seven-field contract, status codes, deployment requirements, policy and limitations.
