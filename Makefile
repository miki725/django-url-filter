.PHONY: clean-pyc clean-build docs clean
ADDITIONAL_COVERAGE_FLAGS ?=
INSTALL_FILE ?= requirements-dev.txt
INSTALL_LOG ?= /dev/stdout

help:  ## show help
	@grep -E '^[a-zA-Z_\-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		cut -d':' -f1- | \
		sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## install all requirements including for testing
	pip install -r $(INSTALL_FILE) 2>&1 > $(INSTALL_LOG)
	pip freeze

clean: clean-build clean-pyc  ## remove all artifacts

clean-build:  ## remove build artifacts
	@rm -rf build/
	@rm -rf dist/
	@rm -rf *.egg-info

clean-pyc:  ## remove Python file artifacts
	-@find . -name '*.pyc' -not -path "./.tox/*" -follow -print0 | xargs -0 rm -f
	-@find . -name '*.pyo' -not -path "./.tox/*" -follow -print0 | xargs -0 rm -f
	-@find . -name '__pycache__' -type d -not -path "./.tox/*" -follow -print0 | xargs -0 rm -rf

clean-test:  ## remove test and coverage artifacts
	rm -rf .coverage coverage*
	rm -rf htmlcov/

clean-test-all: clean-test  ## remove all test-related artifacts including tox
	rm -rf .tox/

lint:  ## lint whole library
	if python -c "import sys; exit(1) if sys.version[:3] < '3.6' or getattr(sys, 'pypy_version_info', None) else exit(0)"; \
	then \
		pre-commit run --all-files ; \
	fi

test:  ## run tests quickly with the default Python
	py.test -sv \
		--cov=django_ufilter \
		--cov-report=term-missing \
		$(ADDITIONAL_COVERAGE_FLAGS) \
		--doctest-modules \
		tests/ django_ufilter/

test-all:  ## run tests on every Python version with tox
	tox

check: lint clean-build clean-pyc clean-test test  ## run all necessary steps to check validity of project

dist: clean  ## build python package ditribution
	check-manifest
	python setup.py sdist bdist_wheel
	ls -l dist
	twine check dist/*

release: clean dist  ## package and upload a release
	twine upload dist/*

syncdb:  ## apply all migrations and load fixtures
	python manage.py migrate
	python manage.py migrate --run-syncdb
	python manage.py loaddata one_to_one many_to_one many_to_many
