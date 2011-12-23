#!/usr/bin/python2
'''
Virtual Filesystems.

Abstract the differences between filesystems into objects that define:
    abspath(path)       - convert path to absolute path/URL
    join(*args)         - join one or more path components
    list(path)          - list files in specified directory
    open(path, mode)    - open a file(-like) object at path
    walk(path, topdown) - walk the filesystem

Use the get_filesystem(url) factory function to access a filesystem
rooted at the specified url or path.

'''

from HTMLParser import HTMLParser
from contextlib import closing
from urllib import unquote
from urllib2 import urlopen, HTTPError
from urlparse import urlsplit, urlunsplit
import errno
import logging
import os

_log = logging.getLogger(__name__)

class NoSuchFileError(RuntimeError):
    '''
    '''
    def __init__(self, *args, **kwargs):
        '''
        '''
        RuntimeError.__init__(self, *args, **kwargs)

class ReadOnlyError(RuntimeError):
    '''
    '''
    def __init__(self, *args, **kwargs):
        '''
        '''
        RuntimeError.__init__(self, *args, **kwargs)

class LocalFilesystem(object):
    '''
    A local (disk-based) filesystem.
    '''
    def __init__(self, basedir):
        '''
        Initialize filesystem.
        '''
        self.basedir = os.path.abspath(urlsplit(basedir).path)

    def __str__(self):
        '''
        Return a string suitable for debugging.
        '''
        return 'localfs:' + self.basedir

    def abspath(self, path):
        '''
        Return the absolute path to the file.

        >>> fs = get_filesystem('file:///etc')
        >>> fs.abspath('group')
        '/etc/group'
        '''
        return os.path.abspath(os.sep.join([self.basedir, path]))

    def join(self, *args):
        '''
        Join one or more path components.

        >>> fs = get_filesystem('/')
        >>> fs.join('/a/', '/b/', '/c/')
        '/a/b/c/'
        >>> fs.join('/a/', '/b', 'c/')
        '/a/b/c/'
        >>> fs.join('a', 'b', 'c')
        'a/b/c'
        '''
        result = [args[0]]
        for arg in args[1:]:
            if result[-1].endswith(os.sep):
                if arg.startswith(os.sep):
                    result.append(arg[1:])
                else:
                    result.append(arg)
            else:
                if not arg.startswith(os.sep):
                    result.append(os.sep)
                result.append(arg)
        return ''.join(result)

    def list(self, path):
        '''
        List files in the specified directory.
        Directory files will be suffixed with '/'.

        >>> fs = get_filesystem('/')
        >>> 'passwd' in fs.list('/etc')
        True
        '''
        path = self.abspath(path)
        if not os.path.isdir(path):
            raise NoSuchFileError(path)
        result = []
        for filename in os.listdir(path):
            if os.path.isdir(self.abspath(filename)):
                filename += os.sep
            result.append(filename)
        return result

    def open(self, path, mode='rb'):
        '''
        Open a file and return a file object.

        >>> fs = get_filesystem('/etc')
        >>> with fs.open('/passwd') as f:
        ...     for line in f:
        ...         if line.startswith('root:'):
        ...             print line.split(':')[2]
        0
        '''
        path = self.abspath(path)
        _log.debug('open %s mode=%s', path, mode)
        if 'w' in mode or 'a' in mode:
            parent = os.path.dirname(path)
            if not os.path.isdir(parent):
                os.makedirs(parent)
        return open(path, mode)

    def walk(self, path, topdown=True):
        '''
        Walk the filesystem starting at the specified path.

        >>> fs = get_filesystem('/etc')
        >>> for root, dirs, files in fs.walk('/'):
        ...     if 'profile' in files:
        ...         print fs.abspath(root)
        ...         print fs.abspath('profile')
        /etc
        /etc/profile
        '''
        path = self.abspath(path)
        for root, dirs, files in os.walk(path, topdown):
            root = root[len(path):]
            if len(root) == 0:
                root = '/'
            yield root, dirs, files

    def rename(self, src, dest):
        '''
        Rename a file.
        '''
        os.rename(self.abspath(src), self.abspath(dest))

    def remove(self, path):
        '''
        Remove a file.
        '''
        try:
            os.remove(self.abspath(path))
        except (OSError, IOError), ex:
            if ex.errno != errno.ENOENT:
                raise

class HttpFilesystem(object):
    '''
    A filesystem backed by a web server.
    '''
    def __init__(self, baseurl):
        '''
        Initialize filesystem.
        '''
        self.baseurl = baseurl

    def __str__(self):
        '''
        Return a string suitable for debugging.
        '''
        return 'httpfs:' + self.baseurl

    def abspath(self, path):
        '''
        Return the absolute URL to the file.

        >>> fs = get_filesystem('http://example.com')
        >>> fs.abspath('/this/or/that')
        'http://example.com/this/or/that'
        >>> fs.abspath('this/or/that')
        'http://example.com/this/or/that'
        '''
        return self.join(self.baseurl, path)

    def join(self, *args):
        '''
        Join one or more path components.

        >>> fs = get_filesystem('http://example.com')
        >>> fs.join('http://example.com', 'abc', '123')
        'http://example.com/abc/123'
        >>> fs.join('x', 'y', 'z')
        'x/y/z'
        '''
        result = [args[0]]
        for arg in args[1:]:
            if result[-1].endswith('/'):
                if arg.startswith('/'):
                    result.append(arg[1:])
                else:
                    result.append(arg)
            else:
                if not arg.startswith('/'):
                    result.append('/')
                result.append(arg)
        return ''.join(result)

    def list(self, path):
        '''
        List files in the specified directory.
        Directory files will be suffixed with '/'.
        '''
        path = self.abspath(path)
        try:
            with closing(urlopen(path)) as fp:
                html = fp.read()
            return HttpFilesystem.html_to_filenames(html)
        except HTTPError:
            raise NoSuchFileError(path)

    def open(self, path, mode='r'):
        '''
        Open a file and return a file-like object.
        '''
        path = self.abspath(path)
        if 'w' in mode or 'a' in mode or '+' in mode:
            raise ReadOnlyError('read-only filesystem: ' + path)
        _log.debug('open %s mode=%s', path, mode)
        return closing(urlopen(path))

    def walk(self, path, topdown=True):
        '''
        Walk the filesystem starting at the specified path.
        '''
        dirs = []
        files = []
        for filename in self.list(path):
            if filename.endswith('/'):
                if filename not in ['./', '../']:
                    dirs.append(filename[:-1])
            else:
                files.append(filename)
        if topdown:
            yield path, dirs, files
        for dirname in dirs:
            subpath = self.join(path, dirname)
            for subroot, subdirs, subfiles in self.walk(subpath, topdown):
                yield subroot, subdirs, subfiles
        if not topdown:
            yield path, dirs, files

    def rename(self, src, unused_dest):
        '''
        Rename a file.
        '''
        raise ReadOnlyError('read-only filesystem: ' + self.abspath(src))

    def remove(self, path):
        '''
        Remove a file.
        '''
        raise ReadOnlyError('read-only filesystem: ' + self.abspath(path))

    @staticmethod
    def html_to_filenames(html):
        '''
        Extract filenames from a typical HTML file listing.
        '''
        class HrefParser(HTMLParser):
            def __init__(self):
                HTMLParser.__init__(self)
                self.hrefs = []
            def handle_starttag(self, tag, attrs):
                if tag == 'a':
                    for unused_name, value in attrs:
                        parts = urlsplit(value)
                        # only consider things that look like files
                        # or directories directly beneath the current dir
                        if '/' not in parts.path[:-1] and \
                           not (parts.scheme or
                                parts.netloc or
                                parts.query or
                                parts.fragment):
                            value = unquote(value)
                            if value not in self.hrefs:
                                self.hrefs.append(value)
        parser = HrefParser()
        parser.feed(html)
        return parser.hrefs

def get_filesystem(url):
    '''
    Return a filesystem rooted at the given URL or path.

    >>> fs = get_filesystem('/foo/bar')
    >>> isinstance(fs, LocalFilesystem)
    True
    >>> fs = get_filesystem('file:///foo/bar')
    >>> isinstance(fs, LocalFilesystem)
    True
    >>> fs = get_filesystem('http://example.com')
    >>> isinstance(fs, HttpFilesystem)
    True
    '''
    scheme = urlsplit(url).scheme
    fs_cls = {
            '':      LocalFilesystem,
            'file':  LocalFilesystem,
            'http':  HttpFilesystem,
            'https': HttpFilesystem,
         }.get(scheme)
    if not fs_cls:
        raise ValueError('unknown protocol "{}"'.format(scheme))
    return fs_cls(url)

def open(url, mode='r'):
    '''
    Open a URL or path.
    '''
    parts = urlsplit(url)
    if parts.scheme in ['', 'file']:
        # An optimization to access local files.
        _log.debug('open %s mode=%s', parts.path, mode)
        return file(parts.path, mode)
    else:
        # Split the URL into a basedir and a filename, use the basedir
        # to create a Filesystem and filename to open the file.
        dirname, filename = os.path.split(parts.path)
        parts = list(parts)
        parts[2] = dirname
        baseurl = urlunsplit(tuple(parts))
        fs = get_filesystem(baseurl)
        return fs.open(filename)
