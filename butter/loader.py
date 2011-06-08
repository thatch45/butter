'''
The butter helper interface for the salt module loader
'''

# Import salt libs
import salt.loader

def statd_maintainers(dirs=[]):
    '''
    Returns the maintainer modules
    '''
    module_dirs = [
        os.path.join(distutils.sysconfig.get_python_lib(), 'butter/statd/maint'),
        ] + dirs
    load = salt.loader.Loader(module_dirs, opts)
    return load.filter_func('maintain')

def statd_data(dirs=[]):
    '''
    Return the data backend modules
    '''
    module_dirs = [
        os.path.join(distutils.sysconfig.get_python_lib(), 'butter/statd/data'),
        ] + dirs
    load = salt.loader.Loader(module_dirs, opts)
    return load.filter_func('data')
