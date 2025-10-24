#!/usr/bin/env bash
set -euo pipefail
echo "▶ Running validation..."
ruff check . || true
pytest -q
echo "✅ Validation complete."
