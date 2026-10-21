#!/usr/bin/env bash
set -euo pipefail
task_backend="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$task_backend"
if [[ ! -x .venv/bin/python ]]; then printf 'Run the root scripts/setup.sh first.\n'; exit 1; fi
task_host="${HOST:-127.0.0.1}"
task_port="${PORT:-8000}"
task_proxies="${FORWARDED_ALLOW_IPS:-}"
proxy_args=(--no-proxy-headers)
if [[ -n "$task_proxies" ]]; then
  proxy_args=(--proxy-headers --forwarded-allow-ips "$task_proxies")
fi
exec .venv/bin/python -m uvicorn main:create_app --factory \
  --host "$task_host" --port "$task_port" --workers 1 "${proxy_args[@]}"
