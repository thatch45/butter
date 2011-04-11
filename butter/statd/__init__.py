'''
The statd subsystem is used to create the stat daemon, this is a system that
uses salt for statistics gathering and system monitoring.
'''
# Import Python modules
import os
import optparse
try:
    import multiprocessing.Process as proc
except:
    import threading.Thread as proc
# Import third party modules
import yaml
# Import Butter modules
import butter.utils
import butter.statd.http
import butter.statd.gather

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
        
        parser.add_option('--config',
                dest='config',
                default='/etc/butter/statd',
                help='Choose an alternative config file for the statd daemon;'\
                   + ' default /etc/butter/statd')

        options, args = parser.parse_args()

        return butter.statd.config.config(options.config)

    def load_procs(self):
        '''
        Create the multiprocessing/threading interfaces for butter statd and start them.
        '''
        http_server = proc(target=butter.statd.http.run)
        http_server.start()
        gather = proc(target=butter.statd.gather.run)
        gather.start()
