#!/bin/bash
# Script to run E2E tests

# 1. Ensure dependencies are installed
python3 -m pip install -r requirements-e2e.txt
python3 -m playwright install chromium

# 2. Run the test
# Assumes the app is already running via docker compose
python3 -m pytest tests/e2e/test_budget_flow.py -v
