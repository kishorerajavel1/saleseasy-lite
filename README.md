# SalesEasy Lite

A field-sales triage application built with FastAPI, Groq/Gemini through LangChain, and React/TypeScript. It separates reported claims from system-recorded inventory and recommends a bounded next step with human review when needed.

Every successful analysis uses strict structured output from the selected real provider, validates its quotations, and applies application-owned business rules. Missing configuration prevents API startup. Provider failures return explicit HTTP errors.

## Submission evidence

| Requirement | Evidence |
|---|---|
| Setup instructions | [Local setup](#local-setup), [backend guide](backend/README.md), [frontend guide](frontend/README.md) |
| Sample inputs and expected outcomes | [Evaluation cases](backend/evaluation/cases.json) and the sample buttons in the UI |
| Evaluation results | [Human-readable report](backend/evaluation/results/groq-results.md) and [complete JSON results](backend/evaluation/results/groq-results.json) |
| Observed weakness and iteration | [Observed live-model iteration](backend/evaluation/observed-iteration.md) |
| Architecture and policy decisions | [Architecture decisions](docs/architecture/decisions.md) and [grounding policy](#grounding-and-review-policy) |
| Known limitations | [Deployment and limits](#deployment-and-limits) |
| AI-tool usage | [AI-tool disclosure](#ai-tool-disclosure) |
| Demo preparation | [Demo script](docs/demo-script.md) |

Deployment and video URLs will be added after the hosted smoke test and recording are complete.

## Local setup

Requirements: Python **3.11+**, Node **22.13+**, and npm. The frontend and backend run independently.

```bash
./scripts/setup.sh
```

If the default Python is older than 3.11, select an interpreter with `PYTHON=python3.12 ./scripts/setup.sh`. Setup creates `backend/.venv`, installs pinned dependencies, and copies environment examples without replacing existing files.

Configure `backend/.env`:

```dotenv
LLM_PROVIDER=groq
GROQ_API_KEY=your-key-here
GROQ_MODEL=openai/gpt-oss-20b
```

Set `LLM_PROVIDER` to `groq` or `gemini`; only the selected provider's key is required. Gemini uses `GEMINI_API_KEY` and `GEMINI_MODEL` (default `gemini-3.8-flash`). An invalid key or unavailable model is reported when an analysis is requested; startup and health checks do not spend model quota. Keep keys server-side.

Configure `frontend/.env.local`:

```dotenv
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Start in separate terminals:

```bash
./scripts/run-backend.sh
```

```bash
./scripts/run-frontend.sh
```

Frontend: [localhost:5173](http://127.0.0.1:5173). API documentation: [localhost:8000/docs](http://127.0.0.1:8000/docs).

The backend allows the two local frontend origins by default. Set `ALLOWED_ORIGINS` to a JSON list for a different frontend URL. All `VITE_` settings are public. Restart each application after changing its configuration.

Component guides: [Backend](backend/README.md) · [Frontend](frontend/README.md).

## Organization

| Directory | Responsibility |
|---|---|
| `backend/controllers/` | HTTP routes, dependencies, safe error responses |
| `backend/services/` | Analysis orchestration, grounding, policy and entity resolution |
| `backend/schemas/` | Strict public response and private LLM interpretation |
| `backend/llm/` | Provider adapters, factory and prompts |
| `backend/repositories/` | Immutable fictional inventory |
| `backend/domain/` | Text normalization and supplementary safety signals |
| `backend/core/`, `middleware/` | Configuration, logging and request limits |
| `backend/tests/` | Isolated policy, network-boundary and API regressions |
| `backend/evaluation/` | Live provider scenarios and reporting |
| `frontend/src/features/` | Triage and inventory components, hooks and API clients |
| `frontend/src/shared/` | HTTP transport, environment and Zod contracts |
| `frontend/src/layouts/`, `styles/` | Application shell and shared styling |

`backend/main.py` constructs the selected provider through `llm/factory.py` and injects it into the analysis service. Controllers only handle the HTTP boundary. Frontend API responses are validated before rendering. See [architecture decisions](docs/architecture/decisions.md).

## API

| Endpoint | Behavior |
|---|---|
| `POST /analyze` | Accept `{"text":"..."}` and return the validated seven-field analysis |
| `GET /inventory` | Read the three fictional catalog records used by policy |
| `GET /health` | Report liveness and selected provider configuration without calling it |
| `GET /status` | Browser-facing alias for service availability checks |

Success contains exactly `issue_category`, `urgency`, `evidence`, `recommended_next_action`, `missing_information`, `needs_human_review`, and `review_reason`.

```bash
curl -i http://127.0.0.1:8000/analyze \
  -H 'Content-Type: application/json' \
  -d '{"text":"Metro Fresh says Cola 500ml is out of stock."}'
```

Expected: inventory discrepancy, physical verification and human review, supported by an unverified quotation and the canonical system stock of 48 units. Recorded stock does not prove shelf availability.

| Status | Meaning |
|---|---|
| `422` | Invalid request or text beyond the 2,000-character cap |
| `413` | Request body beyond the configured cap |
| `429` | Local rate limit; includes `Retry-After` |
| `502` | Blocked/invalid output or rejected credentials, request, or model |
| `503` | Transient provider/network failure after one retry, including quota exhaustion |
| `504` | Local or provider deadline exceeded after one retry |

Analysis failures return `{"code":"...","detail":"..."}`. They never contain a substitute analysis. Transient 429/5xx/network failures and provider deadlines receive one bounded retry; rejected requests and credentials do not. Error messages direct urgent reports to manual review. Raw provider errors and input bodies are not exposed or logged. Request IDs and successful-analysis model/timing metadata remain available through HTTP headers for diagnostics.

## Grounding and review policy

The selected provider returns a private interpretation with observation labels and exact quotations using native JSON-schema output. Code validates the evidence, resolves explicit outlet/SKU aliases and constructs the final response. No autonomous loop, model-controlled tools or commercial write operation exists.

Policy precedence is illness/serious hazard → damage → pricing/commercial demand → stock discrepancy → corroborated stockout → standalone injection → clarification. Independent review flags accumulate without replacing a higher-priority action.

- Reported illness or hazard: critical urgency and quality-team review. Damage alone: high urgency.
- Stock claims conflicting with system inventory: physical verification. Corroborated zero stock: replenishment recommendation.
- Pricing and concessions: authorized human review, with no approval or execution.
- Injection, significant unverified impact and ambiguous entities: human review.
- Field quotes remain unverified. Only relevant canonical inventory rows are verified.
- Unknown pack sizes or multiple outlet/SKU associations require clarification.

The safety detectors supplement a validated provider response. They cannot produce a standalone successful response during an outage. Exact quotation matching establishes traceability rather than truth, and injection containment is not a guarantee against every attack.

## Validation

```bash
./scripts/check.sh
```

Runs backend lint/format checks and isolated tests, then frontend lint/format checks, tests and production build. Tests use network substitutes confined to `backend/tests/` and browser test files; there is no selectable alternative application flow. No API key or network call is needed for those tests.

Run real-model evaluation explicitly from `backend/`:

```bash
.venv/bin/python -m evaluation.run --repeat 3 --delay 15
```

This runs eight live scenarios and one controlled provider-failure scenario three times. Results, failures, latency and prompt/policy versions are written to provider-named files such as `backend/evaluation/results/groq-results.json` and `groq-results.md`. Provider errors count as failures. The simulated case exercises the same production service error contract without calling the provider. Do not equate isolated test passes with live-model performance.

A previous regression found incorrect safety alerts for “nobody is sick” and “no damaged juice packs.” Clause-local negation checks, including within model quotations, address these observed cases. The regression tests remain in `backend/tests/test_policy.py`.

## Deployment and limits

Frontend and backend are independently deployable; there are no Docker files. `render.yaml` defines the one-worker FastAPI service and `netlify.toml` defines the Vite frontend build. On Render, set `GROQ_API_KEY` and set `ALLOWED_ORIGINS` to a JSON list containing the final Netlify origin. On Netlify, set `VITE_API_BASE_URL` to the final Render service URL before building.

Rate and concurrency limits are process-local: the deployment intentionally uses one backend process until shared limiting is added. Render supplies the trusted client address through its proxy; the Blueprint enables proxy headers for that environment. The five-request global window is intentionally conservative for Groq's free quota.

Inventory is static and fictional. English-oriented rules, complex negation, semantic labels, multilingual reports and new attacks require broader evaluation. There is no persistence, review queue, CRM integration or order creation. The UI only recommends actions.

The owner reported successful manual Gemini testing, followed by transient Google `503`/`504` responses that the application now classifies and retries correctly. With Groq `openai/gpt-oss-20b`, all eight live cases passed three paced repetitions (24/24) and the simulated provider failure passed three repetitions (3/3) using prompt `2026-10-21.3`; the saved reports are in `backend/evaluation/results/`. Public deployment verification, recording, final links and actual total time remain submission tasks.

## AI-tool disclosure

OpenAI Codex assisted with planning, implementation, refactoring, tests and documentation. The project owner directed backend reliability, structured evidence, controller/service boundaries, independent deployments, a focused interface and manual code review. Report actual effort and live validation honestly.

## Time spent

Approximately five hours were allocated to planning, implementation, refactoring and evaluation. The final submitted total will include deployment verification and recording time.
