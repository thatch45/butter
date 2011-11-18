# gnumakefile

SHELL=/bin/sh
NOW:=$(shell date +'%Y.%m.%d_%H:%M:%S')
PYTHON:=$(shell type -p python || type -p python2)
PACKAGE:=$(shell $(PYTHON) -c 'from butter.version import PACKAGE; print PACKAGE')
VERSION:=$(shell $(PYTHON) -c 'from butter.version import VERSION; print VERSION')
URL:=$(shell     $(PYTHON) -c 'from butter.version import URL; print URL')
SRCURL:=$(shell  $(PYTHON) -c 'from butter.version import SRCURL; print SRCURL')
TARBALL:=dist/$(PACKAGE)-$(VERSION).tar.gz
PYTHON:=$(shell type -p python || type -p python2)

.PHONY: arch clean clobber coverage default dist install lint test version

default: test

dist: clobber $(TARBALL) arch

clean:
	-rm -rf build cover .coverage MANIFEST
	-rm -rf pkg/arch/{pkg,src,*.gz,*.xz}
	-rm -f pkg/arch/PKGBUILD.local
	-find butter -name \*.py[co] | xargs rm

clobber: clean
	-rm -rf dist

#test:
#	PYTHONPATH=$(PWD) nosetests -s

#coverage:
#	PYTHONPATH=$(PWD) nosetests -s --with-coverage --cover-package=butter --cover-html

lint:
	pylint --rcfile=pylint.cfg butter

$(TARBALL): setup.py butter/*.py butter/*/*.py
	-rm -rf dist build
	PYTHONPATH=$(PWD) nosetests -s
	$(PYTHON) setup.py sdist

install:
	$(PYTHON) setup.py install

version: arch-version
	@echo "# updated version to $(VERSION) in all packages"

# ------------------------------------------------------------------------
# ArchLinux packaging
# ------------------------------------------------------------------------

arch: $(TARBALL)
	echo $(TARBALL)
	mkdir -p dist
	rm -f dist/PKGBUILD* dist/*.pkg.tar.xz
	MD5=$$(md5sum $(TARBALL) | awk '{print $$1}'); \
	sed -e "s|@PACKAGE@|$(PACKAGE)|g; \
	        s|@VERSION@|$(VERSION)|g; \
	        s|@RELEASE@|1|g; \
	        s|@URL@|$(URL)|g; \
	        s|@SOURCE@|$(SRCURL)|g; \
	        s|@MD5@|$$MD5|g; \
	        s|@GIT_BUILD@|no|g;" \
	        < "pkg/arch/PKGBUILD" > "dist/PKGBUILD"
	sed -e "s|^source=.*|source=($(notdir $(TARBALL)))|; \
	        s|^pkgrel=.*|pkgrel=$(NOW)|g" \
	        < "dist/PKGBUILD" > "dist/PKGBUILD.local"
	sed -e "s|@PACKAGE@|$(PACKAGE)|g; \
	        s|@VERSION@|$(VERSION)|g; \
	        s|@RELEASE@|\$$(date +'%Y.%m.%d_%H:%M:%S')|g; \
	        s|@URL@|$(URL)|g; \
	        s|@SOURCE@||g; \
	        s|@MD5@||g; \
	        s|@GIT_BUILD@|yes|g;" \
	        < "pkg/arch/PKGBUILD" > "dist/PKGBUILD.git"
	@echo "# created $(cd dist; ls PKGBUILD*)"
	cd dist; makepkg -cfp PKGBUILD.local --asroot
	rm dist/PKGBUILD.local
	@echo "# created $(ls dist/*xz)"
