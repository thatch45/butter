#!/usr/bin/env python

'''
'''

from butter import convert
from butter import vfs
import errno
import logging
import re
import yaml

_log = logging.getLogger(__name__)

class Config(dict):
    '''
    '''
    def __init__(self, path):
        '''
        Set the location of the config file.
        The location of the config file cannot change while the process
        (e.g. daemon) is running.  You must restart the process to change
        the location of the config file.
        '''
        dict.__init__(self)
        self.path = path
        self.local_fs = None
        self.remote_fs = None
        self.interval_secs = None
        self.regex = None
        self.post_cmd = None
        self.keep = 1

    def load(self):
        '''
        (Re)load configuration from the config file.
        The configuration is not updated if a error occurs while
        reading the file, if the file doesn't contain a dictionary,
        or if the dictionary contains an invalid value.

        Returns True if the configuration was loaded, False otherwise.
        '''
        _log.debug('loading config from {}'.format(self.path))
        newcfg = {}
        try:
            with open(self.path, 'r') as fp:
                newcfg = yaml.safe_load(fp)
                if not newcfg:
                    _log.warn('{}: empty config file'.format(self.path))
                    newcfg = {}
                elif not isinstance(newcfg, dict):
                    _log.error('{}: bad format: not a dict'
                                .format(self.path))
                    return False
        except (OSError, IOError), ex:
            if ex.errno == errno.ENOENT:
                _log.warn('config file does not exist: {}'
                            .format(self.path))
            else:
                _log.error('error reading config file {}'.format(self.path),
                           exc_info=ex)
                return False

        # Add missing values
        if 'images_url' not in newcfg:
            newcfg['images_url'] = 'http://192.168.42.150/archlinux/varch'

        if 'poll_interval' not in newcfg:
            newcfg['poll_interval'] = { 'minutes' : 15 }

        if 'images_dir' not in newcfg:
            newcfg['images_dir'] = '/var/cache/vmcache'

        if 'image_regex' not in newcfg:
            newcfg['image_regex'] = r'(?P<name>[^_]+)_' \
                                    r'(?P<version>\d+(-\d+)?)\.raw\.xz'

        if 'digest_suffix_regex' not in newcfg:
            newcfg['digest_suffix_regex'] = r'\.(?P<digest>sha(\d+)|md5)(sum)?'

        if 'keep' not in newcfg:
            newcfg['keep'] = 1

        # Convert locations to vfs
        new_local_fs = vfs.get_filesystem(newcfg['images_dir'])

        url = newcfg['images_url']
        try:
            new_remote_fs = vfs.get_filesystem(url)
        except ValueError, ex:
            _log.error('{}: invalid image_url: {}'
                        .format(self.path, url),
                        exc_info=ex)
            return False

        # Parse time
        new_interval_secs = convert.to_seconds(newcfg['poll_interval'])
        _log.debug('poll_interval: {} secs'.format(new_interval_secs))

        # Compile regexp
        pattern = '^(?P<image>{image_regex})({digest_suffix_regex})?$' \
                    .format(**newcfg)
        try:
            new_regex = re.compile(pattern)
        except re.error, ex:
            _log.error('{}: invalid regex: {}: {}: check image_regex and '
                       'digest_suffix_regex config values'
                        .format(self.path, ex, pattern))
            return False

        # Silently fix errors
        if newcfg['keep'] < 1:
            newcfg['keep'] = 1

        # Commit the changes
        self.clear()
        self.update(newcfg)
        self.local_fs = new_local_fs
        self.remote_fs = new_remote_fs
        self.interval_secs = new_interval_secs
        self.regex = new_regex
        self.keep = newcfg['keep']
        self.post_cmd = newcfg.get('post_download_cmd')
        return True
