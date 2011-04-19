'''
The stats gathering sequence
'''
# Import python modules
import os
import distutils.sysconfig
# Import salt modules
import salt.client
# Import butter modules
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
        salt.opts = opts
        self.local = salt.client.LocalClient(self.opts['salt-master'])
        self.maint = self.__load_maintainers()

    def __load_maintainers(self):
        '''
        Read in the maintainer functions
        '''
        mods = set()
        maint = {}
        maint_dir = os.path.join(distutils.sysconfig.get_python_lib(),
                'butter/statd/maint')
        for fn_ in os.listdir(maint_dir):
            if fn_.startswith('__init__.py'):
                continue
            if fn_.endswith('.pyo')\
                    or fn_.endswith('.py')\
                    or fn_.endswith('.pyc'):
                mods.add(fn_[:fn_.rindex('.')])
            if fn_.endswith('.pyx') and cython_enable:
                mods.add(fn_[:fn_.rindex('.')])

        for mod in mods:
            if self.opts['disable_returners'].count(mod):
                continue
            try:
                tmodule = __import__('butter.statd.maint', globals(), locals(), [mod])
                module = getattr(tmodule, mod)
                if hasattr(module, '__opts__'):
                    module.__opts__.update(self.opts)
                else:
                    module.__opts__ = self.opts
            except:
                continue
            if hasattr(module, 'clean_old'):
                if callable(module.clean_old):
                    maint[mod] = module
        self.opts['logger'].info('Loaded the following maintainers: '\
                + str(maint))

        return maint

    
