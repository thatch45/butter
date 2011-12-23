#!/usr/bin/env python

'''
The command line interface to vmcache.
'''

from butter.vmcache.config import Config
from butter.vmcache.server import VmCacheDaemon
import argparse
import errno
import logging
import logging.config
import os
import sys

CONFIG_FILE = '/etc/butter/vmcache.conf'
LOG_FILE = '/var/log/butter/vmcache.log'

_log = logging.getLogger(__name__)

def main(argv):
    '''
    Run the vmcache command line utility.
    '''
    try:
        args = _parse(argv[1:])
        if args.debug:
            logging.basicConfig(level=logging.DEBUG, stream=sys.stderr)
        else:
            logging.basicConfig(level=logging.WARNING, stream=sys.stderr)
        config = Config(args.configfile)
        config.load()
        _start_log(config, args)
        args.func(config, args)
    except KeyboardInterrupt:
        sys.stderr.write('interrupted\n')
        return 1

def _parse(args):
    '''
    Parse the command line.
    '''
    parser = argparse.ArgumentParser(description='Manage a cache of VM images.')
    subparsers = parser.add_subparsers()

    # start subcommand
    start_parser = subparsers.add_parser('start', help='start cache server')
    start_parser.set_defaults(func=_start)
    start_parser.add_argument('--foreground',
                              dest='foreground',
                              action='store_true',
                              help='run daemon in the foreground')
    start_parser.add_argument('-c',
                        dest='configfile',
                        default=CONFIG_FILE,
                        help='vmcache config file')
    start_parser.add_argument( '-d',
                         dest='debug',
                         action='store_true',
                         help='debug output' )

    # stop subcommand
    stop_parser = subparsers.add_parser('stop', help='stop cache server')
    stop_parser.add_argument('-c',
                        dest='configfile',
                        default=CONFIG_FILE,
                        help='vmcache config file')
    stop_parser.add_argument( '-d',
                         dest='debug',
                         action='store_true',
                         help='debug output' )
    stop_parser.set_defaults(func=_stop)

    return parser.parse_args(args)

def _start_log(config, args):
    '''
    Configure and start the logging system.
    '''
    if 'logging' in config:
        log_config = config['logging']
    else:
        log_config = {
            'version': 1,
            'formatters': {
                'simple': {
                    'format': '%(asctime)s %(name)s %(levelname)s %(message)s',
                },
            },
            'handlers': {
                'file': {
                    'class':        'logging.FileHandler',
                    'level':        'INFO',
                    'filename':     '/var/log/butter/vmcache.log',
                    'formatter':    'simple',
                    'delay':        'true',
                },
                'console': {
                    'class':      'logging.StreamHandler',
                    'level':      'CRITICAL',
                    'formatter':  'simple',
                    'stream':     'ext://sys.stderr',
                },
            },
            'loggers': {
                'butter':           {}
            },
            'root': {
                'level':            'DEBUG',
                'handlers':         [ 'file', 'console' ]
            },
        }
    logging.config.dictConfig(log_config)

    for handler in logging.getLogger().handlers:
        if hasattr(handler, 'baseFilename'):
            logdir = os.path.dirname(handler.baseFilename)
            try:
                os.makedirs(logdir)
            except OSError, ex:
                if ex.errno != errno.EEXIST:
                    raise
        if args.debug:
            handler.setLevel(logging.DEBUG)

    if 'logging' not in config:
        _log.warning('config file is missing "logging" entry')

def _start(config, args):
    '''
    Start the cache server.
    '''
    daemon = VmCacheDaemon(config, args)
    # Configure daemon
    if not daemon.configure():
        _log.critical('{}: configuration failed'.format(daemon.name))
        sys.exit(1)

    rc = daemon.start(args.foreground)
    if rc == errno.EINVAL:
        msg = '{}: error in config file'.format(daemon.name)
    elif rc == errno.EEXIST:
        msg = '{} is already running'.format(daemon.name)
    elif rc == errno.ESRCH:
        msg = '''
{daemon} does not appear to be running
but the lock file {pidfile} exists.
'''.format(daemon=daemon.name, pidfile=daemon.pidfile.path)
    else:
        msg = '{} returned unexpectedly with rc={}'.format(daemon.name, rc)
    sys.stderr.write(msg.strip())
    sys.stderr.write('\n')
    sys.exit(1)

def _stop(config, args):
    '''
    Stop the cache server.
    '''
    daemon = VmCacheDaemon(config, args)
    daemon.stop()

if __name__ == '__main__':
    main(sys.argv)
