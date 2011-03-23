'''
Initialize interactions with the butter kvm subsytem
'''
import optparse
import sys
import yaml

import butter.kvm.config

def domain():
    '''
    Return the domain name for this system
    '''
    # This is going to need to be more robust
    return subprocess.Popen('dnsdomainname',
            shell=True,
            stdout=subprocess.PIPE).communicate()[0]

class KVM(object):
    '''
    The KVM class is used to wrap the functionality of all butter kvm calls
    '''
    def __init__(self):
        '''
        Set up a KVM object
        '''
        self.opts = self.__gen_opts()

    def __gen_opts(self):
        '''
        Generate the options dict used by butter from cli and configuration
        files
        '''
        cli = self._parse_cli()
        opts = butter.kvm.config.config(cli['config'])
        return opts.union(cli)

    def _parse_cli(self):
        '''
        Parse the butter command line options
        '''
        parser = optparse.OptionParser()
        parser.add_option('-c',
                '--config',
                dest='config',
                default='/etc/butter/kvm.conf')

        options, args = parser.parse_args()

        cli = {}

        cli['config'] = options.config

        # Figure out the fqdn
        dom = domain()
        host = args[-1]
        if host.endswith(dom):
            cli['fqdn'] = host
        else:
            cli['fqdn'] = host + '.' + dom

        return cli

