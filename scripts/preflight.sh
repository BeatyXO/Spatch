#!/usr/bin/env bash
set -euo pipefail
python -m pytest tests -q
if command -v genvm-lint >/dev/null 2>&1; then
  genvm-lint check contracts/spatch.py
else
  echo "genvm-lint is not installed; install genvm-linter before final deployment." >&2
fi
cd frontend
npm test
npm run build
