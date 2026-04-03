lint:
	@echo "## make lint output"
	uv run ruff format src/ tests/
	uv run ruff check --fix src/ tests/
	uv run mypy src/
