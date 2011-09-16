#!/usr/bin/python2

'''
'''

import bz2
import gzip
import os
import shutil
import tarfile
import zipfile

from . import util

NO_COMPRESSOR    = 0x0
GZIP_COMPRESSOR  = 0x1
BZIP2_COMPRESSOR = 0x2
TAR_ARCHIVE      = 0x10
ZIP_ARCHIVE      = 0x20

EXTENSION_HINTS = {
    'gz': GZIP_COMPRESSOR,
    'bz2': BZIP2_COMPRESSOR,
    'raw': NO_COMPRESSOR,
    'tar': TAR_ARCHIVE,
    'zip': ZIP_ARCHIVE,
    'tgz': TAR_ARCHIVE | GZIP_COMPRESSOR,
    'tbz': TAR_ARCHIVE | BZIP2_COMPRESSOR,
    }

_BUFSZ = 8 * 1024

def extract_tar(srcfp, destpath):
    '''
    TODO: 1. Expand symlinks, device files, and FIFOs.
          2. Set file ownership and permissions.
    '''
    with tarfile.open(fileobj=srcfp) as tf:
        for entry in tf:
            path = os.sep.join([destpath, entry.name])
            if entry.isdir():
                util.makedirs(path)
            else:
                util.makedirs(os.path.dirname(path))
                if entry.isreg():
                    datafp = tf.extractfile(entry)
                    with open(path, 'wb') as destfp:
                        shutil.copyfileobj(datafp, destfp)

def extract_zip(srcfp, destpath):
    '''
    TODO: 1. Set file ownership and permissions.
    '''
    with zipfile.ZipFile(srcfp) as zf:
        for entry in zf.infolist():
            path = os.sep.join([destpath, entry.filename])
            if path.endswith('/'):
                util.makedirs(path)
            else:
                util.makedirs(os.path.dirname(path))
                with zf.open(entry) as datafp:
                    with open(path, 'wb') as destfp:
                        shutil.copyfileobj(datafp, destfp)

def uncompress_gz(srcfp, destpath):
    srcfp = gzip.GzipFile(fileobj=srcfp)
    copy(srcfp, destpath)

def uncompress_bz2(srcfp, destpath):
    decompressor = bz2.BZ2Decompressor()
    with open(destpath, 'wb') as destfp:
        while True:
            buf = srcfp.read(_BUFSZ)
            if len(buf) == 0:
                break
            out = decompressor.decompress(buf)
            destfp.write(out)

def copy(srcfp, destpath):
    with open(destpath, 'wb') as destfp:
        shutil.copyfileobj(srcfp, destfp)

def extract(src, destpath, hints=0):
    if isinstance(src, basestring):
        do_close = True
        src = open(src, 'rb')
    else:
        do_close = False

    if hints & TAR_ARCHIVE:
        action = extract_tar
    elif hints & ZIP_ARCHIVE:
        action = extract_zip
    elif hints & GZIP_COMPRESSOR:
        action = uncompress_gz
    elif hints & BZIP2_COMPRESSOR:
        action = uncompress_bz2
    else:
        action = copy
    action(src, destpath)

    if do_close:
        src.close()
