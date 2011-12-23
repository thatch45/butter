#!/usr/bin/env python

'''
'''
import hashlib
import logging
import os
import shutil

_log = logging.getLogger(__name__)

class Image(object):
    '''
    An image on either a local or remote filesystem.
    An image consists of two files: the actual image file and a digest
    file that contains the SHA* or MD5 digest of the image file.
    '''
    def __init__(self, img_id):
        '''
        Initialize an empty image.
        '''
        self.img_id = img_id
        self.fs = None
        self.name = None
        self.version = None
        self.image_path = None
        self.digest_path = None
        self.digest_type = None

    def __repr__(self):
        '''
        Use the image name as the representation so we can specify
        just the image instead of image.img_id to string formatting.
        '''
        return self.img_id

    def __cmp__(self, other):
        '''
        Order images lexigraphically by name and then version.
        '''
        return cmp(self.name, other.name) or cmp(self.version, other.version)

    def is_valid(self):
        '''
        Is the image valid, i.e. is there both image and digest files?
        This does not imply that the digest matches the image contents.
        '''
        return self.image_path and self.digest_path

    def add_file(self, fs, path, attrs):
        '''
        Add an image or digest file to the image.
        '''
        self.fs = fs
        self.name = attrs['name']
        self.version = attrs['version']
        if attrs['digest']:
            self.digest_path = path
            self.digest_type = attrs['digest']
        else:
            self.image_path = path

    def delete(self):
        '''
        Delete the iamge and digest files.
        '''
        for path in [self.image_path, self.digest_path]:
            _log.debug('delete: {}'.format(self.fs.abspath(path)))
            self.fs.remove(path)

    def download(self, dest_fs):
        '''
        Download the image and digest files to a temporary location,
        verify the digest matches the image, and move the files to the
        top of the dest_fs filesystem.
        Returns an Image on the dest_fs filesystem or None if an error
                occurred during download or if the digest doesn't match.
        '''
        pid = os.getpid()
        dest_image  = '/{}'.format(os.path.basename(self.image_path))
        dest_digest = '/{}'.format(os.path.basename(self.digest_path))
        parent      = os.path.basename(self.image_path)
        tmp_image   = '/.{}.download.{}'.format(parent, pid)
        parent      = os.path.basename(self.digest_path)
        tmp_digest  = '/.{}.download.{}'.format(parent, pid)

        try:
            # copy files
            for src, tmp in [(self.image_path, tmp_image),
                             (self.digest_path, tmp_digest)]:
                _log.debug('download {} to {}'.format(self.fs.abspath(src),
                                                      dest_fs.abspath(tmp)))
                with self.fs.open(src, 'rb') as infp:
                    with dest_fs.open(tmp, 'wb') as outfp:
                        shutil.copyfileobj(infp, outfp)
            # verify digest
            expected = self._read_digest(dest_fs, tmp_digest)
            actual = self._compute_digest(dest_fs, tmp_image, self.digest_type)
            if actual != expected:
                _log.error('{} digest does not match {}: {!r} != {!r}'
                            .format(self.digest_type,
                                    dest_fs.abspath(dest_image),
                                    actual, expected))
            else:
                try:
                    dest_fs.rename(tmp_image, dest_image)
                    dest_fs.rename(tmp_digest, dest_digest)
                    _log.info('downloaded {} and {}'
                                .format(dest_fs.abspath(dest_image),
                                        dest_fs.abspath(dest_digest)))
                    img = Image(self.img_id)
                    img.fs = dest_fs
                    img.name = self.name
                    img.version = self.version
                    img.image_path = dest_image
                    img.digest_path = dest_digest
                    img.digest_type = self.digest_type
                    return img
                except:
                    _log.error('failed to rename {} and/or {}'
                                    .format(dest_fs.abspath(tmp_image),
                                            dest_fs.abspath(tmp_digest)),
                                exc_info=True)
                    dest_fs.remove(dest_image)
                    dest_fs.remove(dest_digest)
                    raise
        finally:
            dest_fs.remove(tmp_image)
            dest_fs.remove(tmp_digest)
        return None

    def _read_digest(self, fs, path):
        '''
        Read the digest from the digest file.
        It is always the first word on the first line.
        '''
        with fs.open(path, 'rb') as fp:
            digest = fp.read(8192)
        if digest:
            digest = digest.split()[0]
        return digest

    def _compute_digest(self, fs, path, algorithm):
        '''
        Compute the digest of a file.
        '''
        digestor = hashlib.new(algorithm)
        with fs.open(path, 'rb') as fp:
            buf = fp.read(8192)
            while buf:
                digestor.update(buf)
                buf = fp.read(8192)
        return digestor.hexdigest()

class Images(dict):
    '''
    A dictionary of all valid images found on a filesystem.
    '''
    def __init__(self, fs, regex):
        '''
        Initialize the dictionary with the contents of a filesystem.
        This method walks the filesystem and remembers images that
        match the given regex pattern.
        '''
        dict.__init__(self)
        _log.debug('scanning {}'.format(fs.abspath('/')))
        for root, unused_dirs, files in fs.walk('/'):
            for filename in files:
                if root == '/':
                    path = '/' + filename
                else:
                    path = root + '/' + filename
                match = regex.match(filename)
                if match:
                    attrs = match.groupdict()
                    img_id = attrs['image']
                    _log.debug('add {}'.format(fs.abspath(path)))
                    self[img_id].add_file(fs, path, attrs)
                else:
                    _log.debug('ignore {}: does not match regex'
                                .format(fs.abspath(path)))
        rmlist = []
        for name, img in sorted(self.iteritems()):
            if not img.is_valid():
                rmlist.append(name)
        if rmlist:
            _log.debug('ignore {} invalid images: {}'
                        .format(len(rmlist), ', '.join(rmlist)))
            for name in rmlist:
                del self[name]

        if _log.isEnabledFor(logging.DEBUG):
            _log.debug('found {} valid images'.format(len(self)))
            for img in self.values():
                _log.debug('valid image: {}'.format(img))

    def __missing__(self, img_id):
        '''
        Create a missing image given the image name.
        '''
        value = Image(img_id)
        self[img_id] = value
        return value

    def names(self):
        '''
        Return the set of image names inside the dictionary.
        This is not the same as img_id (the dictionary's key) which is
        the basename of the image file.
        '''
        names = set()
        for img in self.values():
            names.add(img.name)
        return names

    def latest(self, name):
        '''
        Find the latest named image.
        '''
        latest = None
        for img in self.values():
            if img.name != name:
                continue
            if latest is not None and img < latest:
                continue
            if latest is None:
                latest = img
            elif latest < img:
                latest = img
        return latest

    def images(self, name):
        '''
        Return a list of named images ordered by version where oldest
        version is at the beginning of the list.
        '''
        images = []
        for img in self.values():
            if img.name == name:
                images.append(img)
        images.sort()
        return images

    def delete(self, img_id):
        '''
        Delete the image and digest files.
        '''
        img = self.get(img_id)
        if img:
            _log.info('delete {} {}'.format(img.name, img.version))
            del self[img_id]
            img.delete()
