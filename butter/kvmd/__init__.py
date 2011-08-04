'''
Initialize interactions with the butter kvm subsytem
'''
# Import Python libs
import logging
import optparse
import os
import subprocess
import sys
import time

# Import third party libs
import yaml

# Import butter libs
import butter.kvmd.daemon
import butter.log

log = logging.getLogger(__name__)

class KVMD(object):
    '''
    The butter kvm subsystem daemon
    '''
    def __init__(self):
        self.cli = self.__parse_cli()
        self.opts = self.__parse(self.cli['config'])

    def __parse_cli(self):
        '''
        Parse the command line options passed to the butter kvm daemon
        '''
        prog = " ".join([os.path.basename(sys.argv[0]), sys.argv[1]])
        parser = optparse.OptionParser(prog=prog)
        parser.add_option('-f',
                '--foreground',
                default=False,
                action='store_true',
                dest='foreground',
                help='Run the clay daemon in the foreground')

        parser.add_option('-c',
                '--config',
                default='/etc/butter/kvmd',
                dest='config',
                help='Pass in an alternative configuration file')

        parser.add_option('-l',
                '--log-level',
                dest='log_level',
                default='warning',
                choices=butter.log.LOG_LEVELS.keys(),
                help='Console log level. One of %s. For the logfile settings '
                     'see the config file. Default: \'%%default\'.' %
                     ', '.join([repr(l) for l in butter.log.LOG_LEVELS.keys()]))

        options, args = parser.parse_args()

        butter.log.setup_console_logger(options.log_level)

        return {'foreground': options.foreground,
                'config': options.config}

    def __parse(self, conf):
        '''
        Parse the clay deamon configuration file
        '''
        opts = {}

        opts['images'] = '/srv/vm/images'
        opts['pool_size'] = '5'
        opts['keep_old'] = '2'
        opts['interval'] = '5'
        opts['image_source'] = ''
        opts['distros'] = 'arch'
        opts['format'] = 'raw'

        if os.path.isfile(conf):
            try:
                opts.update(yaml.load(open(self.cli['config'], 'r')))
            except:
                pass

        return opts

    def run(self):
        '''
        Starts the buter kvm  daemon
        '''
        kvmd = butter.kvmd.daemon.Daemon(self.opts)
        if not self.cli['foreground']:
            butter.utils.daemonize()
        kvmd.watch_pool()

