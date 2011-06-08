'''
The butter helper interface for the salt module loader
'''

# Import salt libs
import salt.loader

def statd_data(dirs=[]):
    '''
    Return the data backend modules
    '''
    module_dirs = [
        os.path.join(distutils.sysconfig.get_python_lib(), 'butter/statd/data'),
        ] + dirs
    load = salt.loader.Loader(module_dirs, opts)
    return load.gen_functions()

def statd_alert(dirs=[]):
    '''
    Return the data backend modules
    '''
    module_dirs = [
        os.path.join(distutils.sysconfig.get_python_lib(), 'butter/statd/alert'),
        ] + dirs
    load = salt.loader.Loader(module_dirs, opts)
    return load.filter_func('alert')

