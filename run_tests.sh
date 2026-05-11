#!/usr/bin/env bash
# Test runner
#
# Usage:
#   ./run_tests.sh                        — anonimizációs tesztek (mind a 15)
#   ./run_tests.sh test_names_only        — egy teszt név szerint
#   ./run_tests.sh --list                 — összes elérhető teszt listája
#   ./run_tests.sh --ragas                — RAGAS metrika tesztek (Faithfulness + Relevancy)
#   ./run_tests.sh --ragas test_faithfulness_grounded  — egy RAGAS teszt név szerint
#   ./run_tests.sh --all                  — minden teszt együtt

set -e
cd "$(dirname "$0")"

source .venv/bin/activate 2>/dev/null || true

if [ "$1" = "--list" ]; then
    echo "Anonimizációs tesztek:"
    python -m pytest tests/test_anonymization.py --collect-only -q 2>&1 \
        | grep "::" | sed 's/.*::/  /'
    echo ""
    echo "RAGAS metrika tesztek:"
    python -m pytest tests/test_ragas_metrics.py --collect-only -q 2>&1 \
        | grep "::" | sed 's/.*::/  /'
elif [ "$1" = "--ragas" ]; then
    if [ -n "$2" ]; then
        python -m pytest "tests/test_ragas_metrics.py::$2" -v -s
    else
        python -m pytest tests/test_ragas_metrics.py -v -s
    fi
elif [ "$1" = "--all" ]; then
    python -m pytest tests/ -v -s
elif [ -n "$1" ]; then
    python -m pytest "tests/test_anonymization.py::$1" -v -s
else
    python -m pytest tests/test_anonymization.py -v -s
fi
