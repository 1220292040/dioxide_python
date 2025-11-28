.PHONY: help install-poetry install update shell show-deps test test-all test-account test-block test-contract test-serialization demo run clean format lint check-gitignore

help:
	@echo "Dioxide Python SDK - Makefile Commands"
	@echo "======================================"
	@echo "install-poetry  - Install Poetry package manager"
	@echo "install         - Install project dependencies"
	@echo "update          - Update dependencies"
	@echo "shell           - Activate virtual environment"
	@echo "show-deps       - Show installed dependencies"
	@echo "test            - Run all tests in tests/ directory"
	@echo "test-all        - Run all tests (alias for test)"
	@echo "test-account    - Run account tests"
	@echo "test-block      - Run block tests"
	@echo "test-contract   - Run contract tests"
	@echo "test-serialization - Run serialization tests"
	@echo "demo            - Run demo.py script"
	@echo "run             - Run demo.py (alias for demo)"
	@echo "clean           - Clean generated files and caches"
	@echo "format          - Format code with black (if installed)"
	@echo "lint            - Run linters (if installed)"
	@echo "check-gitignore - Check if .gitignore exists"

install-poetry:
	@echo "Checking for Poetry..."
	@which poetry > /dev/null 2>&1 && echo "Poetry is already installed" || \
		(echo "Installing Poetry..." && curl -sSL https://install.python-poetry.org | python3 -)
	@echo "Poetry version:"
	@poetry --version

install: install-poetry
	@echo "Checking for Python 3.11..."
	@if command -v python3.11 > /dev/null 2>&1; then \
		echo "Using Python 3.11 for Poetry environment..."; \
		poetry env use python3.11 || poetry env use $(which python3.11); \
	elif command -v python3.12 > /dev/null 2>&1; then \
		echo "Using Python 3.12 for Poetry environment..."; \
		poetry env use python3.12 || poetry env use $(which python3.12); \
	else \
		echo "Warning: Python 3.11 or 3.12 not found, using default python3"; \
		echo "Note: ed25519==1.5 may not work with Python 3.13"; \
	fi
	@echo "Installing dependencies..."
	@poetry install
	@echo "Dependencies installed successfully!"

update: install-poetry
	@echo "Updating dependencies..."
	@poetry update
	@echo "Dependencies updated successfully!"

shell: install-poetry
	@echo "Activating virtual environment..."
	@poetry shell

show-deps: install-poetry
	@echo "Installed dependencies:"
	@poetry show

test:
	@echo "Running all tests..."
	@for test_file in tests/*_test.py; do \
		echo ""; \
		echo "======================================"; \
		echo "Running $$test_file"; \
		echo "======================================"; \
		poetry run python $$test_file || true; \
	done
	@echo ""
	@echo "All tests completed!"

test-all: test

test-account:
	@echo "Running account tests..."
	@poetry run python tests/account_test.py

test-block:
	@echo "Running block tests..."
	@poetry run python tests/block_test.py

test-contract:
	@echo "Running contract tests..."
	@poetry run python tests/contract_test.py

test-serialization:
	@echo "Running serialization tests..."
	@poetry run python tests/serialization_test.py
	@poetry run python tests/serde_args_test.py

demo:
	@echo "Running demo.py..."
	@poetry run python demo.py

run: demo

clean:
	@echo "Cleaning up..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf build/ dist/ .pytest_cache/ .coverage htmlcov/
	@echo "Cleanup complete!"

format:
	@if command -v poetry > /dev/null && poetry run which black > /dev/null 2>&1; then \
		echo "Formatting code with black..."; \
		poetry run black dioxide_python_sdk/ tests/ demo.py; \
	else \
		echo "black not installed. Install with: poetry add --group dev black"; \
	fi

lint:
	@if command -v poetry > /dev/null && poetry run which flake8 > /dev/null 2>&1; then \
		echo "Running flake8..."; \
		poetry run flake8 dioxide_python_sdk/ tests/; \
	else \
		echo "flake8 not installed. Install with: poetry add --group dev flake8"; \
	fi

check-gitignore:
	@if [ -f .gitignore ]; then \
		echo ".gitignore exists"; \
		echo "Content:"; \
		cat .gitignore; \
	else \
		echo ".gitignore does not exist"; \
	fi
