'''
Load up the configuration for butter
'''
# What goes in the configuration file?
# Paths
# overlay components
# Daemon components - like managing dnsmasq
# static hypervisors?
import os
import yaml

def prepend_root_dir(opts, path_options):
    '''
    Prepends the options that represent filesystem paths with value of the
    'root_dir' option.
    '''
    for path_option in path_options:
        opts[path_option] = os.path.normpath(
                os.sep.join([opts['root_dir'], opts[path_option]]))

def config(path='/etc/butter/statd'):
    '''
    Load up the configuration for butter kvm
    '''
    opts = {'interval': 10,
            'alert_window': 30,
            'alerter': ['email'],
            'sampling_frame': 10,
            'master_config': '/etc/salt/master',
            'statd_config': path,
            'keep_data': 365,
            'returner': 'mongo_return',
            'data_backend': 'mongo',
            'disable_data': [],
            'data_dirs': [],
            'alert_dirs': [],
            'target': '.*',
            'target_type': 'pcre',
            'stats': {},

            # Log options
            'root_dir': '/',
            'log_file' : '/var/log/butter/statd',
            'log_level' : 'warning',
            'log_granular_levels': {},
            }

    if os.path.isfile(path):
        try:
            opts.update(yaml.load(open(path, 'r')))
        except:
            pass

    # Prepend root_dir to other paths
    prepend_root_dir(opts, ['log_file'])

    return opts
