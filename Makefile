PYTHON ?= python
VENV_ACTIVATE = . .venv/bin/activate

.PHONY: help dev-install test test-quiet lint lint-fix precommit-install precommit-run smoke bump build check-dist release-check

help:
	@echo "Targets:"
	@echo "  make dev-install          Install development dependencies"
	@echo "  make test                 Run full unit test suite"
	@echo "  make test-quiet           Run tests with minimal output"
	@echo "  make lint                 Run ruff lint checks"
	@echo "  make lint-fix             Auto-fix ruff issues where possible"
	@echo "  make precommit-install    Install pre-commit hooks"
	@echo "  make precommit-run        Run pre-commit hooks for videocontext files"
	@echo "  make smoke URL=<url>      Run optional live smoke test"
	@echo "  make bump V=0.2.0         Bump package version"
	@echo "  make build                Build sdist and wheel"
	@echo "  make check-dist           Validate built artifacts with twine"
	@echo "  make release-check        Test + build + artifact validation"

test:
	@$(VENV_ACTIVATE) && $(PYTHON) -m unittest discover -s tests -v

test-quiet:
	@$(VENV_ACTIVATE) && $(PYTHON) -m unittest discover -s tests -q

dev-install:
	@$(VENV_ACTIVATE) && $(PYTHON) -m pip install --upgrade -e ".[dev,test]"

lint:
	@$(VENV_ACTIVATE) && $(PYTHON) -m ruff --version >/dev/null || (echo "ruff is not installed. Run: make dev-install"; exit 1)
	@$(VENV_ACTIVATE) && $(PYTHON) -m ruff check .

lint-fix:
	@$(VENV_ACTIVATE) && $(PYTHON) -m ruff --version >/dev/null || (echo "ruff is not installed. Run: make dev-install"; exit 1)
	@$(VENV_ACTIVATE) && $(PYTHON) -m ruff check . --fix

precommit-install:
	@$(VENV_ACTIVATE) && $(PYTHON) -m pre_commit --version >/dev/null || (echo "pre-commit is not installed. Run: make dev-install"; exit 1)
	@$(VENV_ACTIVATE) && cd /home/soloarch/claude_journey && $(PYTHON) -m pre_commit install --config projects/videocontext/.pre-commit-config.yaml

precommit-run:
	@$(VENV_ACTIVATE) && $(PYTHON) -m pre_commit --version >/dev/null || (echo "pre-commit is not installed. Run: make dev-install"; exit 1)
	@$(VENV_ACTIVATE) && cd /home/soloarch/claude_journey && $(PYTHON) -m pre_commit run --config projects/videocontext/.pre-commit-config.yaml --files $$(git ls-files projects/videocontext)

smoke:
	@$(VENV_ACTIVATE) && ./scripts/smoke_e2e.sh "$(URL)" "$(OUT)"

bump:
	@if [ -z "$(V)" ]; then echo "Usage: make bump V=0.2.0"; exit 1; fi
	@$(VENV_ACTIVATE) && $(PYTHON) scripts/bump_version.py "$(V)"

build:
	@$(VENV_ACTIVATE) && $(PYTHON) -m pip install --quiet --upgrade build
	@$(VENV_ACTIVATE) && $(PYTHON) -m build --sdist --wheel

check-dist:
	@$(VENV_ACTIVATE) && $(PYTHON) -m pip install --quiet --upgrade twine
	@$(VENV_ACTIVATE) && $(PYTHON) -m twine check dist/*

release-check: test build check-dist
