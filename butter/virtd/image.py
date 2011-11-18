#!/usr/bin/python2

'''
Source images.

An image consists of two files:
    1. The actual image file, possibly a tar or zip file,
       possibly compressed.  The image is automatically expanded
       if the filename ends with:
            .gz, .bz2
            .raw, .raw.gz, .raw.bz2
            .tar, .tar.gz, .tar.bz2, .tgz, .tbz
            .zip
    2. A checksum file that contains md5sum/shasum output.
       The first word in the file must be the hex checksum.  The checksum
       filename must end with:
            .md5, .md5sum
            .sha1, .sha1sum, .sha256, .sha256sum, .sha512, .sha512sum

'''

import hashlib
import logging
import os
import re
import shutil

from . import archive
from . import util
from . import vfs

log = logging.getLogger(__name__)

_BUFSZ = 8 * 1024

class Image(object):
    '''
    A versioned image.
    '''
    def __init__(self, name=None, version=None, imagepath=None,
                 hashpath=None, hashtype=None):
        '''
        Create an image.
        '''
        self.name = name
        self.imagepath = imagepath
        self.hashpath = hashpath
        self.hashtype = hashtype
        self.version = version

    def __repr__(self):
        '''
        Represent the object as a named tuple for debugging.
        '''
        return '(name={!r} version={!r} imagepath={!r}, hashtype={!r}, ' \
               'hashpath={!r})' \
                    .format(self.name, self.version, self.imagepath,
                            self.hashtype, self.hashpath)

    def is_valid(self):
        '''
        Is the image valid, e.g. do we know where the image and hash
        files are?
        '''
        return bool(self.imagepath and self.hashpath and self.hashtype)

    def checksum_matches(self):
        '''
        Does the computed hash digest equal the expected digest?
        '''
        if not self.imagepath:
            return False
        if not self.hashpath:
            return False
        # Read the expected hash
        with vfs.open(self.hashpath, 'r') as f:
            words = f.read(_BUFSZ).split()
            if not words:
                return False
            expected = words[0]
        # Compute the actual hash
        digest = hashlib.new(self.hashtype)
        with vfs.open(self.imagepath, 'rb') as f:
            while True:
                buf = f.read(_BUFSZ)
                if len(buf) == 0:
                    break
                digest.update(buf)
        actual = digest.hexdigest()
        return actual == expected

    def download(self, destdir):
        '''
        Download the image and checksum to a local directory.
        '''
        destdir = os.path.abspath(destdir)
        util.makedirs(destdir)
        for path in [self.imagepath, self.hashpath]:
            destfile = os.path.basename(path)
            destpath = os.path.join(destdir, destfile)
            with vfs.open(path) as srcfp:
                with open(destpath, 'wb') as destfp:
                    shutil.copyfileobj(srcfp, destfp)

    def move(self, destdir):
        '''
        Move a local image to destdir.
        '''
        destdir = os.path.abspath(destdir)
        util.makedirs(destdir)
        if self.imagepath is not None:
            destpath = os.path.join(destdir, os.path.basename(self.imagepath))
            os.rename(self.imagepath, destpath)
            self.imagepath = destpath
        if self.hashpath is not None:
            destpath = os.path.join(destdir, os.path.basename(self.hashpath))
            os.rename(self.hashpath, destpath)
            self.hashpath = destpath

    def extract(self, destpath):
        '''
        Uncompress, unarchive, and copy image to destpath.
        '''
        destpath = os.path.abspath(destpath)
        util.makedirs(os.path.dirname(destpath))
        hints = 0
        for ext in reversed(self.imagepath.split('.')):
            exthint = archive.EXTENSION_HINTS.get(ext)
            if exthint is None:
                break
            hints |= exthint
        archive.extract(vfs.open(self.imagepath, 'rb'), destpath, hints)
                             
class ImageVersions(dict):
    '''
    A dictionary of all versions of one image.
    '''
    def _get_or_create(self, image, version):
        '''
        Get an image by version name.  If it doesn't exist, create it.
        '''
        img = self.get(version)
        if img is None:
            img = Image(image, version)
            self[version] = img
        return img

    def latest(self):
        '''
        Get most recent image (by version number).
        By default, sorts the version names in reverse alphabetic order
        and returns the first valid image.
        '''
        for version, image in reversed(sorted(self.iteritems())):
            if image.is_valid():
                return image
        return None

class Images(dict):
    '''
    A dictionary describing all known images arranged by name and version.
    '''
    def __init__(self, url=None):
        '''
        Create and optionally load the images dictionary.
        '''
        if url is not None:
            self.load(url)

    def _get_or_create(self, name, version):
        '''
        Get an image by name and version.  If it doesn't exist, create it.
        '''
        versions = self.get(name)
        if versions is None:
            versions = ImageVersions()
            self[name] = versions
        image = versions._get_or_create(name, version)
        return image

    def load(self, url, recursive=True,
             pattern=r'^(?P<name>.*?)_(?P<version>\d{8}(-\d+)?)'):
        '''
        Load images found at or beneath the specified URL/path.
        url       = the top directory to recursively search
        recursive = should recursively examine subdirectories?
        pattern   = a regular expression describing how to split filenames
                    into image names and image version numbers.  The default
                    pattern splits names like 'arch_20001231-1.raw' into
                    'arch' and '20001231-1'.
        An image is composed of the image file itself (possibly an
        archive and possibly compressed) plus a checksum or hash file
        used to verify image file contents.

        Returns self so that you can chain object creation and configuration.
        '''
        matcher = re.compile(pattern)
        fs = vfs.get_filesystem(url)
        for root, dirs, files in fs.walk('/'):
            for filename in files:
                path = fs.abspath(fs.join(root, filename))
                name, suffix = os.path.splitext(filename)
                if suffix.startswith('.'):
                    suffix = suffix[1:]
                if suffix.endswith('sum'):
                    suffix = suffix[:-3]
                m = matcher.match(filename)
                attrs = m.groupdict() if m else {}
                name = attrs.get('name', name)
                version = attrs.get('version', None)
                image = self._get_or_create(name, version)
                if suffix in hashlib.algorithms:
                    if image.hashpath and image.hashpath != path:
                        log.warning('"%s" hash found in %s and %s',
                                    name, image.hashpath, path)
                    image.hashpath = path
                    image.hashtype = suffix
                else:
                    if image.imagepath and image.imagepath != path:
                        log.warning('"%s" image found in %s and %s',
                                    name, image.imagepath, path)
                    image.imagepath = path
            if not recursive:
                break
        return self

    def latest(self, imagename):
        '''
        '''
        versions = self.get(imagename)
        return versions.latest() if versions else None
