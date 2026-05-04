#!/usr/bin/env bash
# Anonymization test runner
#
# Usage:
#   ./run_tests.sh               — run all 15 tests
#   ./run_tests.sh test_names_only   — run one test by name
#   ./run_tests.sh --list            — list all available tests

set -e
cd "$(dirname "$0")"

source .venv/bin/activate 2>/dev/null || true

if [ "$1" = "--list" ]; then
    echo "Available tests:"
    python -m pytest tests/test_anonymization.py --collect-only -q 2>&1 \
        | grep "::" | sed 's/.*::/  /'
elif [ -n "$1" ]; then
    python -m pytest "tests/test_anonymization.py::$1" -v -s
else
    python -m pytest tests/test_anonymization.py -v -s
fi
