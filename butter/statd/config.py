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
    opts = {'interval': 30,
            'master_config': '/etc/salt/master',
            'statd_config': path,
            'keep_data': 365,
            'returner': 'mongo_return',
            'disable_maintainers': [],
            'disable_data': [],
            'maintainer_dirs': [],
            'data_dirs': [],
            'target': '*',
            'target_type': 'glob',
            }
    if os.path.isfile(path):
        try:
            opts.update(yaml.load(open(path, 'r')))
        except:
            pass

    opts['cmd'] = []
    opts['arg'] = []
    for cmd, arg in opts['commands'].items():
        opts['cmd'].append(cmd)
        opts['arg'].append(arg)

    return opts