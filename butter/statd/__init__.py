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
