'''
Load configuration for butter virtd.
'''
import yaml

def load_config(path='/etc/butter/virtd'):
    '''
    Load configuration for butter virtd.
    '''
    opts = {
        'image_source': 'http://192.168.42.150/archlinux/varch',
        'image_dest': '/srv/vm/images',
        'image_pattern': r'archdev_(?P<version>)-\d+.(?P<format>raw|qcow|qcom2|vmdk|vdi)(\.gz)?',
        'digest_pattern': r'archdev_(?P<version>)-\d+.(?P<digest>sha(\d+)|md5)sum',
        'sync_interval': {'days': '1'},
        'keep_for': {'days': '1' },
        }

    try:
        with open(path, 'r') as fp:
            cfg = yaml.load(fp.read())
            if cfg:
                opts.update(cfg)
    except (IOError, OSError):
        pass

    return opts
