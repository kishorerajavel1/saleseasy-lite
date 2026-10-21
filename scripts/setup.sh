#!/usr/bin/env bash
set -euo pipefail
task_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$task_root"
if [[ ! -x backend/.venv/bin/python ]]; then
  task_python="${PYTHON:-python3}"
  "$task_python" -c 'import sys; assert sys.version_info >= (3,11), "Python 3.11+ is required (set PYTHON to its executable)."'
  "$task_python" -m venv backend/.venv
fi
backend/.venv/bin/python -m pip install -r backend/requirements-dev.txt -c backend/requirements.lock.txt
if [[ ! -f backend/.env ]]; then cp backend/.env.example backend/.env; fi
if [[ ! -f frontend/.env.local ]]; then cp frontend/.env.example frontend/.env.local; fi
npm --prefix frontend ci
npm --prefix frontend run build
printf '\nSetup complete. Configure the selected provider key in backend/.env, then run ./scripts/run-backend.sh and ./scripts/run-frontend.sh in separate terminals.\n'
