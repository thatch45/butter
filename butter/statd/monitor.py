'''
Reads the data returned from the gather system and executes any alerts
'''
# Import Python Libs
import datetime
# Import butter libs
import butter.loader

class Monitor(object):
    '''
    This class manages a loop that watches changes in a statd data backend
    '''
    def __init__(self, opts):
        self.opts = opts
        self.data = buter.loader.statd_data(self.opts['data_dirs'])

    def fresh_data():
        '''
        Return the data set as it is configured
        '''
