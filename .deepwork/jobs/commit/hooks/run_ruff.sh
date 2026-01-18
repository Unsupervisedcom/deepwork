#!/bin/bash
cd /Users/noah/Documents/GitHub/deep-work
uv run ruff format --check src/ tests/ && uv run ruff check src/ tests/
