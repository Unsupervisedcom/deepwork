# `make lint` mirrors CI (.github/workflows/validate.yml) in check-only mode
# so that a clean local run guarantees CI will pass. Use `make lint-fix` to
# auto-fix formatter and linter issues locally.

.PHONY: lint lint-fix

lint:
	@echo "## make lint output (check-only — matches CI)"
	uv run ruff format --check src/ tests/
	uv run ruff check src/ tests/
	uv run mypy src/

lint-fix:
	@echo "## make lint-fix output (auto-fix)"
	uv run ruff format src/ tests/
	uv run ruff check --fix src/ tests/
	uv run mypy src/
