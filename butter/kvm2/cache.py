'''
'''
import os
import random
import shutil
import string

from . import util
from .image import Images

class ImageCache(object):
    '''
    The cache for one image.
    Usually the cache will only contain the most recent image version,
    but, while updating to a new version, there can be multiple versions.
    '''
    def __init__(self, imagename, srcurl, cachedir, num_prealloc=5):
        '''
        '''
        self.imagename = imagename
        self.srcurl = srcurl
        self.cachedir = cachedir
        self.num_prealloc = num_prealloc

    def fetch(self, destpath):
        '''
        Fetch an expanded image to destpath.
        Restriction: destpath and the cachedir must be in the same
        filesystem.
        '''
        destpath = os.path.abspath(destpath)
        if os.path.exists(destpath):
            raise IOError('already exists: ' + destpath)
        while True:
            img = self.latest()
            preallocdir = os.path.join(self.cachedir, img.version)
            util.makedirs(preallocdir)
            files = os.listdir(preallocdir)
            if len(files) == 0:
                # There are no preallocated images.  Expand the image
                # directly into destpath.
                img.extract(destpath)
                break
            else:
                srcpath = os.path.join(preallocdir, files[0])
                try:
                    os.rename(srcpath, destpath)
                    # We successfully fetched the preallocated image.
                    break
                except OSError, ex:
                    # If srcpath is missing, someone fetched or trashed
                    # the preallocated image before we could move it.
                    # Otherwise a real error (permission denied) occurred.
                    if os.path.exists(srcpath):
                        raise
        preallocate(preallocdir, img, self.num_prealloc)
        reclaim(self.cachedir, img)

    def latest(self):
        '''
        Get the latest cached image.
        Update the cache if it is outdated.
        '''
        cached_img = None
        while cached_img is None or cached_img.version < src_img.version:
            src_images = Images().load(self.srcurl)
            cached_images = Images().load(self.cachedir, recursive=False)
            src_img = src_images.latest(self.imagename)
            if src_img is None:
                raise KeyError('no such image: ' + self.imagename)
            cached_img = cached_images.latest(self.imagename)
            if cached_img is None or cached_img.version < src_img.version:
                cached_img = self.cache(src_img)
        return cached_img

    def cache(self, src_img):
        '''
        Download the latest image to the cache.
        '''
        tmpdir = ".".join([self.cachedir, "download", str(os.getpid())])
        util.makedirs(tmpdir)
        try:
            src_img.download(tmpdir)
            cached_img = Images(tmpdir).latest(self.imagename)
            if not cached_img.checksum_matches():
                raise IOError('checksum mismatch: {}, {} '.format(
                                src_img.imagepath,
                                src_img.hashpath))
            cached_img.move(self.cachedir)
        finally:
            util.remove(tmpdir)
        return cached_img

def reclaim(targetdir, latest_image):
    '''
    Remove obsolete version caches.
    '''
    print "XXX SPIN UP RECLAIM IN ANOTHER PROCESS"
    targetdir = os.path.abspath(targetdir)
    trashdir = '.'.join([targetdir, 'trash', str(os.getpid())])
    fullname = '_'.join([latest_image.name, latest_image.version]) # HACK
    util.makedirs(trashdir)
    try:
        for name in os.listdir(targetdir):
            path = os.path.join(targetdir, name)
            if os.path.isdir(path):
                if name < latest_image.version:
                    os.rename(path, os.path.join(trashdir, name))
            elif name < fullname and \
                    '.download.' not in name and \
                    '.prealloc.' not in name:
                os.rename(path, os.path.join(trashdir, name))
    finally:
        shutil.rmtree(trashdir)

def preallocate(destdir, img, num):
    '''
    '''
    print "XXX SPIN UP PREALLOC IN ANOTHER PROCESS"
    destdir = os.path.abspath(destdir)
    tmppath = '.'.join([destdir, 'prealloc', str(os.getpid())])
    if not img.checksum_matches():
        raise IOError('checksum mismatch: {}, {} '.format(
                        img.imagepath,
                        img.hashpath))
    util.makedirs(destdir)
    try:
        while len(os.listdir(destdir)) < num:
            img.extract(tmppath)
            rename_to_random(tmppath, destdir)
    except (IOError, OSError):
        # destdir disappeared ... we're probably creating an
        # obsolete preallocation and someone else is reaping
        # old images.  Discontinue preallocation.  Someone else
        # is preallocating a more recent image.
        pass

def rename_to_random(path, destdir):
    '''
    Rename a file to a unique, random name inside destdir.
    '''
    while os.path.exists(path):
        name = ''.join([random.choice(string.digits) for i in range(10)])
        destpath = os.path.join(destdir, name)
        try:
            os.rename(path, destpath)
            return destpath
        except OSError:
            if not os.path.exists(destpath):
                raise
