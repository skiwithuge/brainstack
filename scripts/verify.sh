#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "==================================="
echo "Starting Agent Verification Process"
echo "==================================="

# 1. Enforce Virtual Environment Usage
# We check if $VIRTUAL_ENV is set or if we are running in an environment that looks like a venv.
if [[ -z "${VIRTUAL_ENV}" ]]; then
    # If not explicitly in a venv, check if a venv directory exists that we can use
    if [ ! -d "venv" ]; then
        echo "❌ FAILED: No 'venv' directory found and \$VIRTUAL_ENV is not set."
        echo "Agents MUST execute all work inside the isolated virtual environment."
        exit 1
    fi
    echo "⚠️ \$VIRTUAL_ENV is not set, but 'venv' exists. Assuming execution context is safe."
    PYTHON_CMD="./venv/bin/python"
else
    echo "✅ Running inside active virtual environment: ${VIRTUAL_ENV}"
    PYTHON_CMD="python"
fi

# 2. Syntax Check (Sanity)
echo "Checking Python syntax in 'src', 'tests', and root files..."
find . -name "*.py" -not -path "./venv/*" -not -path "./.venv/*" -exec $PYTHON_CMD -m py_compile {} +
echo "✅ Syntax check passed."

# 3. Functional Execution Tests
echo "Running standard library functional test suite..."
$PYTHON_CMD -m unittest discover tests/
echo "✅ Tests passed."

echo "==================================="
echo "All validation checks passed."
echo "You may now mark this task as complete!"
echo "==================================="
exit 0
