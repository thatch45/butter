'''
The statd subsystem is used to create the stat daemon, this is a system
that uses salt for statistics system monitoring.
'''
# Import Python modules
import optparse
import os
import sys

# Import third party modules
import yaml

# Import Butter modules
import butter.log
import butter.statd.config
import butter.statd.monitor
import butter.utils

log = butter.log.getLogger(__name__)

def verify_env(dirs):
    '''
    Verify that the named directories are in place and that the environment
    can shake the salt
    '''
    for dir_ in dirs:
        if not os.path.isdir(dir_):
            try:
                os.makedirs(dir_)
            except OSError, e:
                print 'Failed to create directory path "%s" - %s' % (dir_, e)

class StatD(object):
    '''
    The StatD object is used to initialize the stats monitoring subsytem
    for butter
    '''
    def __init__(self):
        self.opts = self.__parse()

    def __parse(self):
        '''
        Parse the command line options and load the configuration
        '''
        prog = " ".join([os.path.basename(sys.argv[0]), sys.argv[1]])
        parser = optparse.OptionParser(prog=prog)
        
        parser.add_option('-d',
                '--daemon',
                dest='daemon',
                default=False,
                action='store_true',
                help='Daemonoize the process.')

        parser.add_option('--config',
                dest='config',
                default='/etc/butter/statd',
                help='Choose an alternative config file for the statd '
                     'daemon; default /etc/butter/statd')

        parser.add_option('-l',
                '--log-level',
                dest='log_level',
                default='warning',
                choices=butter.log.LOG_LEVELS.keys(),
                help='Console log level. One of %s. For the logfile settings '
                     'see the config file. Default: \'%%default\'.' %
                     ', '.join([repr(l) for l in butter.log.LOG_LEVELS.keys()]))

        options, args = parser.parse_args()

        opts = butter.statd.config.config(options.config)

        opts['daemon'] = options.daemon

        for name, level in opts['log_granular_levels'].iteritems():
            butter.log.set_logger_level(name, level)

        butter.log.setup_console_logger(options.log_level)

        return opts

    def run(self):
        '''
        Start butter statd.
        '''
        verify_env([os.path.dirname(self.opts['log_file'])])
        butter.log.setup_logfile_logger(self.opts['log_file'], self.opts['log_level'])

        if self.opts['daemon']:
            butter.utils.daemonize()
        monitor = butter.statd.monitor.Monitor(self.opts)
        monitor.run()
