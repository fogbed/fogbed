MININET = src/mininet/*.py
TEST = src/mininet/test/*.py
EXAMPLES = src/mininet/examples/*.py
MN = bin/mn
PYMN = python -B bin/mn
BIN = $(MN)
PYSRC = $(MININET) $(TEST) $(EXAMPLES) $(BIN)
MNEXEC = mnexec
MANPAGES = mn.1 mnexec.1
P8IGN = E251,E201,E302,E202,E126,E127,E203,E226
BINDIR = /usr/bin
MANDIR = /usr/share/man/man1
DOCDIRS = docs/doxygen/html docs/doxygen/latex
PDF = docs/doxygen/latex/refman.pdf

CFLAGS += -Wall -Wextra

all: codecheck test

clean:
	rm -rf build dist *.egg-info *.pyc $(MNEXEC) $(MANPAGES) $(DOCDIRS)

codecheck: $(PYSRC)
	-echo "Running code check"
	util/versioncheck.py
	pyflakes $(PYSRC)
	pylint --rcfile=.pylint $(PYSRC)
#	Exclude miniedit from pep8 checking for now
	pep8 --repeat --ignore=$(P8IGN) `ls $(PYSRC) | grep -v miniedit.py`

errcheck: $(PYSRC)
	-echo "Running check for errors only"
	pyflakes $(PYSRC)
	pylint -E --rcfile=.pylint $(PYSRC)

test: $(MININET) $(TEST)
	-echo "Running tests"
	src/mininet/test/test_nets.py
	src/mininet/test/test_hifi.py

slowtest: $(MININET)
	-echo "Running slower tests (walkthrough, examples)"
	src/mininet/test/test_walkthrough.py -v
	src/mininet/examples/test/runner.py -v

mnexec: mnexec.c $(MN) src/mininet/net.py
	cc $(CFLAGS) $(LDFLAGS) -DVERSION=\"`PYTHONPATH=. $(PYMN) --version`\" $< -o $@

install: $(MNEXEC) $(MANPAGES)
	install $(MNEXEC) $(BINDIR)
	install $(MANPAGES) $(MANDIR)
	python setup.py install

maxinstall:
	mkdir -p /usr/local/share/maxinet
	cp -rv src/maxinet/Frontend/examples /usr/local/share/maxinet/
	chmod +x /usr/local/share/maxinet/examples/*
	cp share/MaxiNet-cfg-sample /usr/local/share/maxinet/config.example
	cp share/maxinet_plot.py /usr/local/share/maxinet/

maxuninstall:
	rm -rf /usr/local/lib/python2.7/dist-packages/maxinet-*/
	rm -rf /usr/local/share/maxinet
	rm -f /usr/local/bin/FogbedServer /usr/local/bin/FogbedStatus /usr/local/bin/FogbedFrondendServer /usr/local/bin/FogbedWorker

develop: $(MNEXEC) $(MANPAGES)
# 	Perhaps we should link these as well
	install $(MNEXEC) $(BINDIR)
	install $(MANPAGES) $(MANDIR)
	python setup.py develop

man: $(MANPAGES)

mn.1: $(MN)
	PYTHONPATH=. help2man -N -n "create a Mininet network." \
	--no-discard-stderr "$(PYMN)" -o $@

mnexec.1: mnexec
	help2man -N -n "execution utility for Mininet." \
	-h "-h" -v "-v" --no-discard-stderr ./$< -o $@

.PHONY: doc

doc: man
	mkdir -p $(DOCDIRS)
	doxygen docs/doxygen/doxygen.cfg
	make -C docs/doxygen/latex
