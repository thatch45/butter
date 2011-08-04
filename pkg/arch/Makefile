# Convenience targets for building and installing Arch packages
# prior to committing changes to git.

local:
	-rm -rf ../../build
	makepkg -f -p PKGBUILD-local --asroot
	rm -rf pkg

install: local
	-yes | pacman -R butter-local
	yes | pacman -U butter-local-*

