# Convenience targets for building and installing Arch packages
# prior to committing changes to git.

local:
	-rm -rf ../../build
	-rm butter-local*.tar.xz
	makepkg -f -p PKGBUILD-local --asroot
	-rm -rf pkg ../../build

install: local
	-yes | pacman -R butter-local
	yes | pacman -U butter-local-*
