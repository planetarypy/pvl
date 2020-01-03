.PHONY: clean-pyc clean-build docs clean

help:
	@echo "clean-build - remove build artifacts"
	@echo "clean-pyc - remove Python file artifacts"
	@echo "lint - check style with flake8"
	@echo "test - run tests quickly with the default Python"
	@echo "test-all - run tests on every Python version with tox"
	@echo "coverage - check code coverage quickly with the default Python"
	@echo "docs - generate Sphinx HTML documentation, including API docs"
	@echo "release - package and upload a release"
	@echo "dist - package"

clean: clean-build clean-pyc
	rm -fr htmlcov/

clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr *.egg-info

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -rf {} +
	find . -name '*~' -exec rm -f {} +

lint:
	flake8 pvl tests

test:
	python -m pytest

# rtest:
rtest:
	python -m pytest tests/test_grammar.py\
			         tests/test_decoder.py\
					 tests/test_token.py\
					 tests/test_lexer.py\
					 tests/test_parser.py\
					 tests/test_encoder.py\
					 tests/test_init.py

test-all:
	tox

coverage:
	py.test --cov pvl --cov-report html tests
	open htmlcov/index.html

docs:
	rm -f docs/pvl.rst
	rm -f docs/modules.rst
	sphinx-apidoc -o docs/ pvl
	$(MAKE) -C docs clean
	$(MAKE) -C docs html
	open docs/_build/html/index.html

release: clean
	python setup.py sdist upload
	python setup.py bdist_wheel upload

dist: clean
	python setup.py sdist
	python setup.py bdist_wheel
	ls -l dist
