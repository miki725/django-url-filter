.PHONY: clean-pyc clean-build docs clean

help:
	@echo "install - install all requirements including for testing"
	@echo "install-quite - same as install but pipes all output to /dev/null"
	@echo "clean - remove all artifacts"
	@echo "clean-build - remove build artifacts"
	@echo "clean-pyc - remove Python file artifacts"
	@echo "clean-test - remove test and coverage artifacts"
	@echo "clean-test-all - remove all test-related artifacts including tox"
	@echo "lint - check style with flake8"
	@echo "test - run tests quickly with the default Python"
	@echo "test-coverage - run tests with coverage report"
	@echo "test-all - run tests on every Python version with tox"
	@echo "check - run all necessary steps to check validity of project"
	@echo "release - package and upload a release"
	@echo "dist - package"

install:
	pip install -r requirements-dev.txt

install-quite:
	pip install -r requirements-dev.txt > /dev/null

clean: clean-build clean-pyc

clean-build:
	@rm -rf build/
	@rm -rf dist/
	@rm -rf *.egg-info

clean-pyc:
	-@find . -name '*.pyc' -not -path "./.tox/*" -follow -print0 | xargs -0 rm -f
	-@find . -name '*.pyo' -not -path "./.tox/*" -follow -print0 | xargs -0 rm -f
	-@find . -name '__pycache__' -type d -not -path "./.tox/*" -follow -print0 | xargs -0 rm -rf

clean-test:
	rm -rf .coverage coverage*
	rm -rf htmlcov/

clean-test-all: clean-test
	rm -rf .tox/

importanize:
	importanize --ci

lint:
	flake8 .
	python --version | grep "Python 3" && make importanize || true

test:
	py.test -sv --cov=url_filter --cov-report=term-missing --doctest-modules tests/ url_filter/

test-all:
	tox

check: lint clean-build clean-pyc clean-test test

release: clean
	python setup.py sdist upload
	python setup.py bdist_wheel upload

dist: clean
	python setup.py sdist
	python setup.py bdist_wheel
	ls -l dist
