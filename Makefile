MAP ?= maps/easy/01_linear_path.txt

install:
	uv sync

run:
	uv run python main.py $(MAP)

plain:
	uv run python main.py $(MAP) --plain

debug:
	uv run python -m pdb main.py $(MAP)

clean:
	find . -name "__pycache__" -not -path "./.venv/*" -exec rm -rf {} +
	rm -rf .mypy_cache

lint:
	uv run flake8 .
	uv run mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	uv run flake8 .
	uv run mypy . --strict

.PHONY: install run plain debug clean lint lint-strict