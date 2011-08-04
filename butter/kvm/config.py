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

def config(path='/etc/butter/kvm'):
    '''
    Load up the configuration for butter kvm
    '''
    opts = {'images': '/srv/vm/images',
            'instances': '/srv/vm/instances',
            'local_path': '/mnt/local/vm',
            'salt_pki': '/etc/salt/pki',
            # Log options
            'root_dir': '/',
            'log_file' : '/var/log/butter/kvm',
            'log_level' : 'warning',
            'log_granular_levels': {},
            # Global vm generation options
            'storage_type': 'local', # Can be 'local', 'shared', 'choose'
            'distro': 'arch', # The default distribution to use
            # A dict of network bridges bound to the respective interface
            # name on the vm
            'network': {'br0', 'eth0'},
            'graphics': 'vnc', # Set to vnc or spice
            # Where to place the udev networking file in the overlay
            'udev': '/etc/udev/rules.d/70-persistent-net.rules',
            'dnsmasq': '',
            'puppet': 0,
            }
    if os.path.isfile(path):
        try:
            opts.update(yaml.load(open(path, 'r')))
        except:
            pass

    # Prepend root_dir to other paths
    prepend_root_dir(opts, ['log_file'])

    return opts
