# Local verification

The focused interface and real-provider-only flow were verified locally on 21 October 2026.

| Check | Result |
|---|---|
| Backend policy/service/API/provider regression suite | 83 passed |
| Frontend transport and workflow suite | 10 passed |
| Backend Ruff lint and formatting | Passed |
| Frontend ESLint and Prettier | Passed |
| TypeScript and Vite production build | Passed |

The provider-failure contract returns explicit HTTP errors. Startup requires the selected Groq or Gemini configuration. Tests include structured provider-status classification, one bounded retry for transient failures and deadlines, a validation repair, rejected fabricated quotes, provider refusal, timeout/concurrency, safe errors, CORS, input/body/rate limits and safety precedence. Frontend tests cover failed requests without a substitute result, safe text rendering, stale-result removal and duplicate-submit prevention.

Network calls are substituted only inside isolated tests. A 200-request concurrent service soak completed with zero exceptions and schema-valid results. Live evaluation uses the selected real provider and writes expected/actual reports. The owner reported successful manual Gemini testing. During stability testing, minimal LangChain calls and a raw Google SDK call received provider `503`/`504` responses across several listed Flash models. This isolates that failure to Google rather than the prompt, structured output, or LangChain. The adapter classifies those statuses and the service retries them once.

The first Groq live evaluation passed six of seven cases but classified “Stock is low at one of the stores” as a complete stockout. Prompt version `2026-10-21.2` distinguishes low stock from unavailable/zero stock. This is the observed weakness used for the required evaluation iteration.

After that correction, all seven original live cases passed three quota-paced repetitions against Groq `openai/gpt-oss-20b` (21/21). A later relevance audit added an eighth live case for irrelevant messages and a formal simulated-failure entry. All nine entries then passed three repetitions: 24/24 live and 3/3 simulated. Real-model probes also verified greetings, thanks, unrelated questions and routine no-issue updates return low/no-action, while a vague possible business report requests clarification. A final request through the FastAPI HTTP boundary returned 200 with `stock_discrepancy`, `verify_stock_physically`, human review, the configured model header and a request ID. The current isolated gate is 101 backend tests and 10 frontend tests, with both lint/format suites and the frontend production build passing.

Neither application was started during the cleanup. No deployment, commit, push or submission was performed.

The earlier implementation session began at 17:42:31 IST. This note does not establish total effort: include subsequent refactoring, code review and live testing when reporting actual time.
