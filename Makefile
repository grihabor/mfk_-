all: help

venv:
	python3 -m virtualenv venv

.PHONY: help
help:
	@echo "Helper commands for project managements"

.PHONY: install
install:
	python setup.py install

