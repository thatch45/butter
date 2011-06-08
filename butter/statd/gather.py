'''
The stats gathering sequence
'''
# Import python modules
import os
import distutils.sysconfig
import time
# Import salt modules
import salt.client
# Import butter modules
import butter.loader
import butter.statd.maint

# Import cython 
cython_enable = False
try:
    import pyximport; pyximport.install()
    cython_enable = True
except:
    pass

class Gather(object):
    '''
    The Gather class is used to run sequential status gather calls on the 
    minions and load the data into redis
    '''
    def __init__(self, opts):
        self.opts = opts
        self.local = salt.client.LocalClient(self.opts['master_config'])

    def stat_cmd(self):
        '''
        Execute the salt command to inform the minions to return stats
        '''
        cmd = [self.opts['target'],
               self.opts['cmd'],
               self.opts['arg'],
               0,
               self.opts['target_type'],
               self.opts['returner']]

        self.local.cmd(*cmd)

    def loop(self):
        '''
        Run the salt stat command loop
        '''
        while True:
            self.stat_cmd()
            time.sleep(self.opts['interval'])

class Maintain(object):
    '''
    Maintain a data source
    '''
    def __init__(self, opts):
        self.opts = opts
        self.maint = butter.loader.statd_maintainers(self.opts['data_dirs'])

    def maintain(self):
        '''
        Run the maintainer functions
        '''
        if self.maint.has_key(self.opts['returner']):
            self.maint[self.opts['returner']].clean_old(self.opts['keep_data'])

    def run():
        '''
        Start the maintainer
        '''
        self.maintain()
        time.sleep(self.opts['interval'] * 10)
