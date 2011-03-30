'''
This module is used to gather the live state data used by butter via salt
'''
# Import salt client
import salt.client

class HVStat(object):
    '''
    Detects information about the hypervisors
    '''
    def __init__(self, opts):
        self.opts = opts
        self.local = salt.client.LocalClient()
        self.hypers = self.__hypers()
        self.resources = self.get_resources()

    def __hypers(self):
        '''
        Return a list, suitable for the salt client, of the hypervisors
        '''
        data = self.local.cmd('*', 'virt.is_kvm_hyper')
        hypers = set()
        for hyper in data:
            if data[hyper] == True:
                hypers.add(hyper)
        return list(hypers)

    def get_resources(self):
        '''
        Return the full resources information about the cloud
        '''
        return self.local.cmd(self.hypers,
                'butterkvm.full_butter_data',
                arg=[self.opts['local_path']],
                expr_form='list')

    def system(self, system):
        '''
        Returns the data pertinant to a specific system
        '''
        return system

    def print_system(self, system):
        '''
        Prints out the data to a console about a specific system
        '''
        print self.system(system)

    def print_avail(self):
        '''
        Print the available resources for all hypervisors
        '''
        print 'foo'

    def print_query(self):
        '''
        Prints out the information gathered in a clean way
        '''
        print 'foobar'
