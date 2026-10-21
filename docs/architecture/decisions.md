# Architecture decisions

## Provider interpretation and application-owned policy

Every successful analysis begins with the configured Groq or Gemini provider. The provider factory constructs that adapter and injects it into `AnalysisService`. The provider returns a private `Interpretation` of quoted observations, while the public `Analysis` contains the seven assignment fields.

The service owns concurrency, time budgets and at most two provider calls. It retries transient provider/network failures and deadlines once, while rejected credentials, requests and models fail immediately. Invalid structured output receives one repair attempt. Quotations must exist in the original report. Policy then resolves inventory, enforces safety precedence and builds server-owned questions/review reasons. Supplementary detectors protect against missed known risks within a validated model flow.

Missing configuration prevents startup. Provider failures, timeouts, refusals and exhausted validation return explicit 502/503/504 errors. The application does not construct a successful analysis without validated provider output.

## Responsibilities

Controllers own the HTTP boundary. Services own orchestration, evidence and policy. Schemas define strict contracts. The repository supplies the three immutable fictional inventory records. Each provider adapter owns its LangChain-specific integration; it cannot verify facts or authorize commercial actions. Middleware owns request limits, IDs and security headers.

Network substitutes exist only in tests for repeatable error/timeout assertions. They are not configurable providers or runtime fallback paths. Live evaluation always calls the selected real provider and records failures as failures.

No tools, autonomous loops, persistence, database or vector index are needed for this bounded task. Adding a real inventory source would require explicit freshness and evidence contracts. Multiple backend replicas would require shared limiting.

## Trust and grounding

Explicit aliases resolve one outlet/SKU association. Unknown sizes and ambiguous associations do not receive a verified inventory row. Code constructs canonical inventory evidence, while field quotations always remain unverified. System-recorded stock does not establish physical shelf availability.

Illness/hazards take precedence over damage, pricing, stock conditions, injection and missing information. Pricing and significant unverified impact require human judgment. Actions are recommendations only.

Local negation regressions cover “nobody is sick” and negated damage quotes. Exact quotation matching proves traceability rather than semantic correctness or truth. Broader multilingual/adversarial evaluation remains future work.

## Independent applications

The React frontend calls FastAPI directly across origins. Feature clients validate responses with Zod; hooks own requests; components render data. The compact shell has no account/workspace placeholders. Provider, timing and request IDs are available to developers through API headers rather than displayed in the interface.

The frontend needs a public API URL at build time. The backend needs a server-side key and frontend-origin allowlist. Hosting requires explicit bind/port and trusted-proxy configuration. Rate limits are in memory and assume one process.
