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
