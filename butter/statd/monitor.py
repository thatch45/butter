'''
Reads the data returned from the gather system and executes any alerts
'''
# Import Python Libs
import datetime
import sys
# Import butter libs
import butter.loader

class Monitor(object):
    '''
    This class manages a loop that watches changes in a statd data backend
    '''
    def __init__(self, opts):
        self.opts = opts
        self.data = buter.loader.statd_data(self.opts['data_dirs'])
        self.mine = self.__get_miner()

    def __get_miner(self):
        '''
        Return the function used to mine data
        '''
        name = '{0[data_backend]}_data.mine'.format(self.opts)
        if self.data.has_key(name):
            return self.data[name]
        err = 'Data backend for {0[data_backend]} was not found, check the'\
            + ' "data_backend" configuration value.'
        err.format(self.opts)
        sys.stderr.write(err)
        sys.exit(2)

    def fresh_data(self):
        '''
        Return the data set as it is configured
        '''
        return self.mine(self.opts['sampling_frame'], self.opts['target'])
