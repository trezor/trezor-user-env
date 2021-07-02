PY_FILES = $(shell find . -type f -name '*.py')

style_check:
	isort --version | awk '/VERSION/{print $$2}'
	black --version
	@echo [ISORT]
	@isort --check-only $(PY_FILES)
	@echo [BLACK]
	@black --check $(PY_FILES)

style:
	@echo [ISORT]
	@isort $(PY_FILES)
	@echo [BLACK]
	@black $(PY_FILES)
