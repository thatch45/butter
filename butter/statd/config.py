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
            'target': '.*',
            'target_type': 'pcre',
            'stats': {},
            }

    if os.path.isfile(path):
        try:
            opts.update(yaml.load(open(path, 'r')))
        except:
            pass

    return opts
