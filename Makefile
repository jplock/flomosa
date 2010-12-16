BASE        ?= $(PWD)
BIN          = $(BASE)/bin
PYVERS      := 2.5
PYTHON       = $(BIN)/python$(PYVERS)
PLATFORM     = $(shell uname -s)
EZ_INSTALL  := $(BIN)/easy_install
VIRTUALENV  ?= VIRTUALENV_USE_SETUPTOOLS=1 \
               $(shell test -x `which virtualenv` && which virtualenv || \
                       test -x `which virtualenv-$(PYVERS)` && \
                                which virtualenv-$(PYVERS))
VIRTUALENV  += --no-site-packages
SETUP        = $(PYTHON) setup.py
GIT_HEAD     = $(BASE)/.git/$(shell cut -d\  -f2-999 .git/HEAD)
BUILD_NUMBER ?= 0000INVALID

.PHONY: dev env clean xclean extraclean bundles \
        debian/changelog

sdist:
    $(SETUP) sdist

env: $(PYTHON)

$(PYTHON) $(BIN)/easy_install:
    $(VIRTUALENV) .

dev: env
    $(SETUP) develop

    @echo "        ==============================================================="
    @echo "              To activate your shiny new environment, please run:"
    @echo
    @which figlet > /dev/null && figlet -c " . bin/activate" || \
    echo "                                 . bin/activate"

    @echo "        ==============================================================="

lint flakes:
    $(SETUP) flakes

coverage: .coverage
    @$(COVERAGE) html -d $@ $(COVERED)

coverage.xml: .coverage
    @$(COVERAGE) xml $(COVERED)

.coverage: $(SOURCES) $(TESTS)
    -@$(COVERAGE) run --branch setup.py test -s flomosa.test

bin/coverage: bin/easy_install
    @$(EZ_INSTALL) coverage

prereqs: prereqs-$(PLATFORM)
prereqs-Linux:
    sudo apt-get install python2.5 python2.5-dev python-virtualenv

prereqs-Darwin:
    sudo port install python_select python25 py25-virtualenv
    sudo python_select python25

clean:
    find . -type f -name \*.pyc -exec rm {} \;
    rm -rf *.egg *.egg-info htmlcov build* src* dist coverage \
           build-bundle* _trial_temp

xclean: extraclean
extraclean: clean
    rm -rf .Python bin include lib