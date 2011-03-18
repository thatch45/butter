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

def config(path='/etc/butter/kvm_config'):
    '''
    Load up the configuration for butter kvm
    '''
    opts = {'images': '/srv/vm/images',
            'instances': '/srv/vm/instances',
            'local_path': '/mnt/local/vm',
            'storage_type': 'local', # Can be 'local', 'shared', 'choose'
            'dnsmasq': '',
            'puppet': 0,
            'salt_pki': '/etc/salt/pki'}
    if os.path.isfile(path):
        try:
            opts.update(yaml.load(open(path, 'r')))
        except:
            pass

    return opts
