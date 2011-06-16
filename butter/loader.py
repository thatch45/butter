'''
The butter helper interface for the salt module loader
'''
# Import python libs
import os
import distutils.sysconfig

# Import salt libs
import salt.loader

def statd_data(opts):
    '''
    Return the data backend modules
    '''
    module_dirs = [
        os.path.join(distutils.sysconfig.get_python_lib(), 'butter/statd/data'),
        ] + opts['data_dirs']
    load = salt.loader.Loader(module_dirs, opts)
    return load.gen_functions(opts)

def statd_alert(opts):
    '''
    Return the alerter modules
    '''
    module_dirs = [
        os.path.join(distutils.sysconfig.get_python_lib(), 'butter/statd/alert'),
    ] + opts['alert_dirs']
    load = salt.loader.Loader(module_dirs, opts)
    return load.filter_func('alert')

