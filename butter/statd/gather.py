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

    def construct_arg(self):
        '''
        Return the command and argument constructs derived from the
        configuration, if no configuration is set, butter statd will exit
        '''
        if not self.opts['stats']:
            err = 'No stats configuration has been set, please set up the'\
                + ' stats value in the butter statd configuration file'
            sys.stderr.write(err)
            sys.exit(2)
        cmds = []
        args = []
        for call, data in self.opts['status'].items():
            cmds.append(call)
            if data.has_key('arg'):
                args.append(data['args'])
            else:
                args.append('')
        return cmds, args

    def stat_cmd(self):
        '''
        Execute the salt command to inform the minions to return stats
        '''
        cmds, args = self.construct_cmd()
        cmd = [self.opts['target'],
               cmd,
               arg,
               0,
               self.opts['target_type'],
               self.opts['returner']]

        self.local.cmd(*cmd)

    def run(self):
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
        self.maint = butter.loader.statd_maintainers(self.opts)

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
