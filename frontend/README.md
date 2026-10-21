# SalesEasy Lite frontend

React/TypeScript UI built with Vite. A focused report-and-analysis screen with example updates, collapsible inventory, grounded evidence, review questions and expandable structured JSON.

## Setup and run

Use Node 22.13+:

```bash
npm ci
npm run dev
```

Create `.env.local` from `.env.example` if it does not exist. Set the public API URL:

```dotenv
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Open [localhost:5173](http://127.0.0.1:5173). Start the backend separately. Its `ALLOWED_ORIGINS` must include this frontend origin. Restart Vite after changing configuration. Every `VITE_` value is public; keep API keys on the backend.

## Organization

| Path | Responsibility |
|---|---|
| `src/app/` | Screen composition and workflow tests |
| `src/features/triage/` | Input, examples, results, request lifecycle and feature API |
| `src/features/inventory/` | Collapsible inventory and data loading |
| `src/shared/` | HTTP transport, Zod contracts and environment configuration |
| `src/layouts/`, `src/styles/` | Compact application header, tokens and responsive layout |

API responses are validated before rendering. Field quotations are text nodes. Analysis errors are shown without creating a result; editing clears stale output. Pending requests disable repeat submission and are cancelled on unmount. Diagnostic model/request metadata is kept out of the product interface.

## Validate and build

```bash
npm run lint
npm run format:check
npm test
npm run build
```

The output is `dist/`. The repository-root `netlify.toml` sets the monorepo base, build command, publish directory, security headers and SPA fallback. Set `VITE_API_BASE_URL` to the public Render API URL in Netlify before building.

See the [project README](../README.md) for policy, API behavior, evaluation and limitations.
