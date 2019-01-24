.PHONY: clean-pyc clean-build docs clean

help:  ## show help
	@grep -E '^[a-zA-Z_\-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		cut -d':' -f1- | \
		sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## install all requirements including for testing
	pip install -r requirements-dev.txt

install-quite:  ## same as install but pipes all output to /dev/null
	pip install -r requirements-dev.txt > /dev/null

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

importanize:
	importanize --ci

lint:  ## check style with flake8
	flake8 .
	if python -c "import sys; exit(1) if sys.version[:3] < '3.6' else exit(0)"; \
	then \
		make importanize ; \
	fi

test:  ## run tests quickly with the default Python
	py.test -sv --cov=url_filter --cov-report=term-missing --doctest-modules tests/ url_filter/

test-all:  ## run tests on every Python version with tox
	tox

check: lint clean-build clean-pyc clean-test test  ## run all necessary steps to check validity of project

release: clean  ## package and upload a release
	python setup.py sdist bdist_wheel upload

dist: clean  ## build python package ditribution
	python setup.py sdist bdist_wheel
	ls -l dist

syncdb:  ## apply all migrations and load fixtures
	python manage.py migrate
	python manage.py migrate --run-syncdb
	python manage.py loaddata one_to_one many_to_one many_to_many
