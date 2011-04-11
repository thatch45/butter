'''
The stats gathering sequence
'''
# Import python modules
import os
# Import salt modules
import salt.client

class Gather(object):
    '''
    The Gather class is used to run sequential status gather calls on the 
    minions and load the data into redis
    '''
    def __init__(self, opts):
        salt.opts = opts
        self.local = salt.client.LocalClient(self.opts['salt-master'])

