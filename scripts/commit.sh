#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status
set -e

if [ -z "$1" ]; then
    echo "❌ Error: Commit message is required."
    echo "Usage: ./scripts/commit.sh \"Your commit message\""
    exit 1
fi

COMMIT_MSG="$1"

echo "==================================="
echo "Step 1: Running Verification Suite"
echo "==================================="
# Run the verification script. If it fails, set -e will abort this script.
bash scripts/verify.sh

echo "==================================="
echo "Step 2: Committing Code"
echo "==================================="
git add .
git commit -m "$COMMIT_MSG"

echo "✅ Successfully verified and committed changes!"
