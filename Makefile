PYTHON       = $(BIN)/python2.5
SETUP        = $(PYTHON) setup.py
BUILD_NUMBER ?= 0000INVALID

.PHONY: flomosa/_version.py

sdist:
    $(SETUP) sdist

version: flomosa/_version.py

flomosa/_version.py: flomosa/_version.py.m4
    m4 -D__BUILD__=$(BUILD_NUMBER) $^ > $@