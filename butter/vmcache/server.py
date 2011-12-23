#!/usr/bin/env python

'''
'''
from butter.daemon import Daemon
from butter.vmcache import image
import logging
import os
import time

_log = logging.getLogger(__name__)

class VmCacheDaemon(Daemon):
    '''
    '''
    def __init__(self, config, unused_args):
        '''
        '''
        Daemon.__init__(self, 'vmcache')
        self.config = config

    def configure(self):
        '''
        '''
        return self.config.load()

    def run(self):
        '''
        '''
        while not self.shutdown:
            if self.reconfigure:
                self.configure()
                self.reconfigure = False
            remote = image.Images(self.config.remote_fs,
                                  self.config.regex)
            local = image.Images(self.config.local_fs,
                                 self.config.regex)
            if _log.isEnabledFor(logging.DEBUG):
                rimgs = sorted(remote.keys())
                _log.debug('remote images: {}'.format(
                           ', '.join(rimgs) if rimgs else '<none>'))
                limgs = sorted(local.keys())
                _log.debug('local images: {}'.format(
                           ', '.join(limgs) if limgs else '<none>'))

            for name in sorted(remote.names()):
                # Latest remote image
                latest_remote = remote.latest(name)
                _log.debug('latest remote {} image: {}'
                            .format(name, latest_remote.fs.abspath(
                                        latest_remote.image_path)))
                # Latest local image
                latest_local = local.latest(name)
                if latest_local:
                    _log.debug('latest local {} image: {}'
                                .format(name, latest_local.fs.abspath(
                                            latest_local.image_path)))
                else:
                    _log.debug('no local {} image'.format(name))

                # If local isn't up-to-date, download the remote image
                if latest_local is None or latest_remote > latest_local:
                    _log.info('update {} image to {}'
                                .format(latest_remote.name,
                                        latest_remote.img_id))
                    img = latest_remote.download(self.config.local_fs)
                    if img:
                        local[img.img_id] = img
                        if self.config.post_cmd:
                            imgpath = img.fs.abspath(img.image_path)
                            cmd = self.config.post_cmd.format(image_path=imgpath)
                            _log.info('run: {}'.format(cmd))
                            rc = os.system(cmd)
                            _log.info('exit={}'.format(rc))
                else:
                    _log.debug('local {} image is up-to-date: {}'
                                .format(latest_local.name, latest_local))

                # Prune old images
                images = local.images(name)
                for img in images[:-self.config.keep]:
                    local.delete(img.img_id)

            # Sleep for the poll interval.  We will be awakened if a
            # signal is sent to us, e.g. SIGHUP that will cause us to
            # reread the config file.
            now = time.time()
            _log.debug('sleep {} seconds'.format(self.config.interval_secs))
            time.sleep(self.config.interval_secs)
            _log.debug('slept {} seconds'.format(time.time()-now))
