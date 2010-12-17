PYVERS        = 2.5
PYTHON        = $(shell test -x bin/python$(PYVERS) && \
                    echo bin/python$(PYVERS) || echo `which python$(PYVERS)`)
VIRTUALENV    = $(shell /bin/echo -n `which virtualenv || \
                                      which virtualenv-$(PYVERS) || \
                                      which virtualenv$(PYVERS)`)
VIRTUALENV   += --python=python$(PYVERS) --no-site-packages
COVERAGE      = bin/coverage
SRCDIR       := flomosa
SOURCES      := $(shell find $(SRCDIR) -type f -name \*.py -not -name 'test_*')
TESTS        := $(shell find $(SRCDIR) -type f -name test_\*.py)
COVERED      := $(SOURCES)
SETUP         = $(PYTHON) ./setup.py
EZ_INSTALL    = $(SETUP) easy_install
PYLINT        = bin/pylint --rcfile=.pylintrc
BUILD_NUMBER ?= 1


.PHONEY: test dev clean extraclean

test:
	$(SETUP) test

xunit.xml: bin/nosetests $(SOURCES) $(TESTS)
	$(SETUP) nosetests -w $(SRCDIR)/test --with-xunit --xunit-file=$@

bin/nosetests: bin/easy_install
	@$(EZ_INSTALL) nose

coverage: .coverage
	@$(COVERAGE) html -d $@ $(COVERED)

coverage.xml: .coverage
	@$(COVERAGE) xml $(COVERED)

.coverage: $(SOURCES) $(TESTS) bin/coverage
	-@$(COVERAGE) run --branch --source=$(SRCDIR) setup.py test

bin/coverage: bin/easy_install
	@$(EZ_INSTALL) coverage

bin/pep8: bin/easy_install
	@$(EZ_INSTALL) pep8

pep8: bin/pep8
	@bin/pep8 --repeat $(SRCDIR)

pep8.txt: bin/pep8
	@bin/pep8 --repeat $(SRCDIR) | perl -ple 's/: ([WE]\d+)/: [$1]/' > $@

lint: bin/pylint
	-$(PYLINT) -f colorized $(SRCDIR)

lint.html: bin/pylint
	-$(PYLINT) -f html $(SRCDIR) > $@

lint.txt: bin/pylint
	-$(PYLINT) -f parseable $(SRCDIR) > $@

bin/pylint: bin/easy_install
	@$(EZ_INSTALL) pylint

tags: TAGS.gz

TAGS.gz: TAGS
	gzip $^

TAGS: $(SOURCES)
	ctags -eR .

env: bin/easy_install

bin/easy_install:
	$(VIRTUALENV) .
	-test -f deps/setuptools* && $@ -U deps/setuptools*

dev: develop
develop: env
	nice -n 20 $(SETUP) develop
	@echo "            ---------------------------------------------"
	@echo "            To activate the development environment, run:"
	@echo "                           . bin/activate"
	@echo "            ---------------------------------------------"

clean:
	find . -type f -name \*.pyc -exec rm {} \;
	rm -rf build dist TAGS TAGS.gz flomosa.egg-info tmp .coverage \
	       coverage coverage.xml lint.html lint.txt profile \
	       .profile *.egg xunit.xml pep8.txt

xclean: extraclean
extraclean: clean
	rm -rf bin lib .Python include