check: style_check code_check

style_check:
	isort --version | awk '/VERSION/{print $$2}'
	black --version
	@echo [ISORT]
	@isort --check-only .
	@echo [BLACK]
	@black --check .

style:
	@echo [ISORT]
	@isort .
	@echo [BLACK]
	@black .

code_check:
	@echo [MYPY]
	@mypy .
	@echo [FLAKE8]
	@flake8 .

test:
	pytest -s

test_with_running_controller:
	pytest -s --controller-already-runs

build_dashboard:
	@echo [DASHBOARD BUILD]
	@cd src/dashboard && npm install && npm run build

.PHONY: check style_check style code_check test test_with_running_controller build_dashboard
