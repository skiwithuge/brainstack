# Contributing to Brainstack

We welcome contributions! Brainstack is designed to be a highly deterministic, stable tool. To maintain this, we enforce strict testing via our automated verifiers.

## Development Setup
1. Ensure your IDE is using the local virtual environment.
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
2. Place your credentials inside `.env`.
3. Never bypass our commit scripts.

## The Verification Protocol
You are required to verify your logic before making a Pull Request. Do not use standard `git commit`!
Use our custom verification deploy script:
```bash
./scripts/commit.sh "Your descriptive commit message"
```
This script will automatically run `scripts/verify.sh` to validate syntax and test logic parsing. If your commit fails the suite, it will be rejected.

> **Important**: You must run the tests and the commit script from within the activated virtual environment (`source venv/bin/activate`) to ensure all dependencies are resolved correctly.
