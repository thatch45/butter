# Convenience targets for building and installing Arch packages
# prior to committing changes to git.

local:
	-rm -rf ../../build pkg butter-*.pkg.tar.xz
	if [ "$$(id -u)" -eq 0 ]; \
	then \
	    makepkg -f -p PKGBUILD-local --asroot; \
	else \
	    makepkg -f -p PKGBUILD-local; \
	fi
	-rm -rf pkg ../../build

install: local
	-yes | pacman -R butter-local
	yes | pacman -U butter-local-*
