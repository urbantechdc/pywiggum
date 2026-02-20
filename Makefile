.PHONY: help install test lint type clean build publish

help:
	@echo "PyWiggum Development Commands"
	@echo ""
	@echo "  install     Install package with dev dependencies"
	@echo "  test        Run test suite"
	@echo "  lint        Run ruff linter"
	@echo "  type        Run mypy type checker"
	@echo "  clean       Remove build artifacts"
	@echo "  build       Build package"
	@echo "  publish     Publish to PyPI (requires credentials)"
	@echo ""

install:
	uv pip install -e ".[dev]"

test:
	pytest -v

lint:
	ruff check src/ tests/

type:
	mypy src/pywiggum

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build: clean
	python -m build

publish: build
	twine upload dist/*
