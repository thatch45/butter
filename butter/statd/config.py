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
            'data': {'status.status_all': []},
            }
    if os.path.isfile(path):
        try:
            opts.update(yaml.load(open(path, 'r')))
        except:
            pass

    return opts
