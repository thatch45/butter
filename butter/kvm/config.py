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
            'salt_pki': '/etc/salt/pki',
            # Global vm generation options
            'storage_type': 'local', # Can be 'local', 'shared', 'choose'
            'distro': 'arch', # The default distribution to use
            # A dict of network bridges bound to the respective interface
            # name on the vm and a mac addr prefix to use
            'network': {'br0', ['eth0', '52:54:00']},
            'graphics': 'vnc', # Set to vnc or spice
            'dnsmasq': '',
            'puppet': 0,
            }
    if os.path.isfile(path):
        try:
            opts.update(yaml.load(open(path, 'r')))
        except:
            pass

    return opts
