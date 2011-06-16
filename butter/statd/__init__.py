'''
The statd subsystem is used to create the stat daemon, this is a system that
uses salt for statistics gathering and system monitoring.
'''
# Import Python modules
import os
import optparse
# Import third party modules
import yaml
# Import Butter modules
import butter.utils
import butter.statd.gather
import butter.statd.config
import butter.statd.monitor

class StatD(object):
    '''
    The StatD object is used to initialize the stats gathering and monitoring
    subsytem for butter
    '''
    def __init__(self):
        self.opts = self.__parse()

    def __parse(self):
        '''
        Parse the command line options and load the configuration
        '''
        parser = optparse.OptionParser()
        
        parser.add_option('-d',
                '--daemon',
                dest='daemon',
                default=False,
                action='store_true',
                help='Daemonoize the process.')

        parser.add_option('--config',
                dest='config',
                default='/etc/butter/statd',
                help='Choose an alternative config file for the statd daemon;'\
                   + ' default /etc/butter/statd')

        options, args = parser.parse_args()

        opts = butter.statd.config.config(options.config)

        opts['daemon'] = options.daemon

        return opts

    def run(self):
        '''
        Create the multiprocessing/threading interfaces for butter statd and start them.
        '''
        gather = butter.statd.gather.Gather(self.opts)
        if self.opts['daemon']:
            butter.utils.daemonize()
        if self.opts['stats']:
            monit = butter.statd.monitor.Monitor(self.opts)
            multiprocessing.Process(target=monit.run).start()
        gather.run()
