'''
This module is used to gather the live state data used by butter via salt
'''
# Import salt client
import salt.client

class HVStat(object):
    '''
    Detects information about the hypervisors
    '''
    def __init__(self):
        self.local = salt.client.LocalClient()
        self.hypers = self.__hypers()

    def __hypers(self):
        '''
        Return a list, suitable for the salt client, of the hypervisors
        '''
        data = self.local.cmd('*', 'virt.is_hyper')

