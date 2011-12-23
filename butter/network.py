#!/usr/bin/env python

'''
'''

import re

CLOUDS = {
        'ut' : 1,
        'la' : 2,
        'dv' : 3,
        'qa' : 4,
    }

NETWORKS = {
        'service' : 1,
        'storage' : 2,
        'ipmi'    : 3,
        'boot'    : 4,
    }

DNS_HOST_NUM = '1'
PXE_SERVER_NUM = '1'
GATEWAY_HOST_NUM = '254'

class _IPv4(object):
    '''
    '''
    def __init__(self, groups, network):
        '''
        '''
        cloud_num = CLOUDS[groups['cloud']]
        network_num = NETWORKS[network]
        octets = ['10',
                  str(cloud_num * 10 + network_num),
                  groups['cab'],
                  groups['num']]
        self.addr = '.'.join(octets)
        self.subnet_prefix = '.'.join(octets[:2])
        self.subnet_prefix_reverse = '.'.join(reversed(octets[:2]))
        self.subnet = self.subnet_prefix + '.0.0'
        self.broadcast = self.subnet_prefix + '.255.255'
        self.netmask = '255.255.0.0'
        self.gateway = self.subnet_prefix + '.1.' + GATEWAY_HOST_NUM
        self.dns = self.subnet_prefix + '.1.' + DNS_HOST_NUM
        if network in ['boot', 'ipmi']:
            self.pxe_server = self.subnet_prefix + '.1.' + PXE_SERVER_NUM
        else:
            self.pxe_server = None

    def to_dict(self, prefix=''):
        '''
        '''
        result = {
                prefix + 'addr': self.addr,
                prefix + 'broadcast': self.broadcast,
                prefix + 'dns': self.dns,
                prefix + 'netmask': self.netmask,
                prefix + 'gateway': self.gateway,
                prefix + 'subnet': self.subnet,
                prefix + 'subnet_prefix': self.subnet_prefix,
                prefix + 'subnet_prefix_reverse': self.subnet_prefix_reverse,
            }
        if self.pxe_server is not None:
            result[prefix + 'pxe_server'] = self.pxe_server
        return result

class _Interface(object):
    '''
    '''
    def __init__(self, groups, network, mac_addr=None):
        '''
        '''
        self.ipv4 = _IPv4(groups, network)
        self.hostname = '{type}{num}-{network}-cab{cab}'\
                        .format(network=network, **groups)
        self.fqdn = '{}.{}'.format(self.hostname, groups['domain'])
        self.domain = groups['domain']
        self.domain_reverse = '.'.join(reversed(self.domain.split('.')))
        if mac_addr is None:
            self.mac_addr = None
            self.pxe_addr = None
        else:
            self.mac_addr = mac_addr.upper()
            self.pxe_addr = '01-' + self.mac_addr.replace( ':', '-' )

    def to_dict(self, prefix=''):
        '''
        '''
        result = {
                prefix + 'fqdn': self.fqdn,
                prefix + 'hostname': self.hostname,
                prefix + 'domain': self.domain,
                prefix + 'domain_reverse': self.domain_reverse,
            }
        result.update(self.ipv4.to_dict(prefix + 'ipv4.'))
        if self.mac_addr is not None:
            result[prefix + 'mac_addr'] = self.mac_addr
        if self.pxe_addr is not None:
            result[prefix + 'pxe_addr'] = self.pxe_addr
        return result

class BeyondHost(object):
    '''
    >>> BeyondHost('node123-cab2.hw.dv', \
                       'FF:EE:DD:CC:BB:AA:99:88', \
                       '00:11:22:33:44:55:66:77')
    boot.domain=hw.dv
    boot.domain_reverse=dv.hw
    boot.fqdn=node123-boot-cab2.hw.dv
    boot.hostname=node123-boot-cab2
    boot.ipv4.addr=10.34.2.123
    boot.ipv4.broadcast=10.34.255.255
    boot.ipv4.dns=10.34.1.1
    boot.ipv4.gateway=10.34.1.254
    boot.ipv4.netmask=255.255.0.0
    boot.ipv4.pxe_server=10.34.1.1
    boot.ipv4.subnet=10.34.0.0
    boot.ipv4.subnet_prefix=10.34
    boot.ipv4.subnet_prefix_reverse=34.10
    boot.mac_addr=FF:EE:DD:CC:BB:AA:99:88
    boot.pxe_addr=01-FF-EE-DD-CC-BB-AA-99-88
    cabinet=2
    cloud=3
    domain=hw.dv
    domain_reverse=dv.hw
    fqdn=node123-cab2.hw.dv
    host_num=123
    hostname=node123-cab2
    ipmi.domain=hw.dv
    ipmi.domain_reverse=dv.hw
    ipmi.fqdn=node123-ipmi-cab2.hw.dv
    ipmi.hostname=node123-ipmi-cab2
    ipmi.ipv4.addr=10.33.2.123
    ipmi.ipv4.broadcast=10.33.255.255
    ipmi.ipv4.dns=10.33.1.1
    ipmi.ipv4.gateway=10.33.1.254
    ipmi.ipv4.netmask=255.255.0.0
    ipmi.ipv4.pxe_server=10.33.1.1
    ipmi.ipv4.subnet=10.33.0.0
    ipmi.ipv4.subnet_prefix=10.33
    ipmi.ipv4.subnet_prefix_reverse=33.10
    ipmi.mac_addr=00:11:22:33:44:55:66:77
    ipmi.pxe_addr=01-00-11-22-33-44-55-66-77
    ipv4.addr=10.31.2.123
    ipv4.broadcast=10.31.255.255
    ipv4.dns=10.31.1.1
    ipv4.gateway=10.31.1.254
    ipv4.netmask=255.255.0.0
    ipv4.subnet=10.31.0.0
    ipv4.subnet_prefix=10.31
    ipv4.subnet_prefix_reverse=31.10
    storage.domain=hw.dv
    storage.domain_reverse=dv.hw
    storage.fqdn=node123-storage-cab2.hw.dv
    storage.hostname=node123-storage-cab2
    storage.ipv4.addr=10.32.2.123
    storage.ipv4.broadcast=10.32.255.255
    storage.ipv4.dns=10.32.1.1
    storage.ipv4.gateway=10.32.1.254
    storage.ipv4.netmask=255.255.0.0
    storage.ipv4.subnet=10.32.0.0
    storage.ipv4.subnet_prefix=10.32
    storage.ipv4.subnet_prefix_reverse=32.10
    '''
    FQDN_PATTERN = \
            '(?P<hostname>(?P<type>[a-z]+)(?P<num>\d+)-cab(?P<cab>\d+))\.' \
            '(?P<domain>(?P<env>\w+)\.(?P<cloud>\w+))'
    _pattern = None

    def __init__(self, fqdn, boot_mac_addr=None, ipmi_mac_addr=None):
        '''
        '''
        if self._pattern is None:
            self._pattern = re.compile(self.FQDN_PATTERN)
        m = self._pattern.match(fqdn)
        if not m:
            raise ValueError('{} is not a valid Beyond FQDN'.format(fqdn))
        groups        = m.groupdict()
        self.fqdn     = fqdn
        self.ipv4     = _IPv4(groups, 'service')
        self.hostname = groups['hostname']
        self.domain   = groups['domain']
        self.cloud    = CLOUDS[groups['cloud']]
        self.cabinet  = int(groups['cab'])
        self.host_num = int(groups['num'])
        self.storage  = _Interface(groups, 'storage')
        self.ipmi     = _Interface(groups, 'ipmi', ipmi_mac_addr)
        self.boot     = _Interface(groups, 'boot', boot_mac_addr)
        self.domain_reverse = '.'.join(reversed(groups['domain'].split('.')))
        self.pxe_server = self.boot.ipv4.addr

    def __repr__(self):
        '''
        '''
        buf = ""
        for k, v in sorted(self.to_dict().iteritems()):
            buf += '{}={}\n'.format(k, v)
        return buf.rstrip()

    def to_dict(self, prefix=''):
        '''
        '''
        result = {
                prefix + 'fqdn': self.fqdn,
                prefix + 'hostname': self.hostname,
                prefix + 'domain': self.domain,
                prefix + 'domain_reverse': self.domain_reverse,
                prefix + 'cloud': self.cloud,
                prefix + 'cabinet': self.cabinet,
                prefix + 'host_num': self.host_num,
            }
        result.update(self.ipv4.to_dict(prefix + 'ipv4.'))
        result.update(self.storage.to_dict(prefix + 'storage.'))
        result.update(self.ipmi.to_dict(prefix + 'ipmi.'))
        result.update(self.boot.to_dict(prefix + 'boot.'))
        return result

if __name__ == "__main__":
    import doctest
    doctest.testmod()

    x = BeyondHost('node1-cab2.hw.dv',
                   'FF:EE:DD:CC:BB:AA:99:88',
                   '00:11:22:33:44:55:66:77')
    for k, v in sorted(x.to_dict('host.').iteritems()):
        print '{}={}'.format(k, v)
