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

        parser.add_option('-C',
                '--create',
                dest='create',
                default=False,
                action='store_true',
                help='Set the creation flag')

        parser.add_option('-D',
                '--destroy',
                dest='destroy',
                default=False,
                action='store_true',
                help='Force quit the named vm')

        parser.add_option('-P',
                '--purge',
                dest='purge',
                default=False,
                action='store_true',
                help='Recursively destroy and delete the named vm')

        parser.add_option('-Q',
                '--query',
                dest='query',
                default=False,
                action='store_true',
                help='Set the query flag')

        parser.add_option('-M',
                '--migrate',
                dest='migrate',
                default=False,
                action='store_true',
                help='Set the migrate flag')

        parser.add_option('-R',
                '--reset',
                dest='reset',
                default=False,
                action="store_true",
                help='Hard reset a vm')

        parser.add_option('-c',
                '--cpus',
                dest='cpus',
                type=int,
                default=1,
                help='The number of cpus to give the vm - only read for new'\
                        + 'virtual machines; default = 1')

        parser.add_option('-m',
                '--mem',
                '--memory',
                dest='mem',
                type=int,
                default=1024,
                help='The amount of ram to give the vm in mebibytes - only read'\
                        + ' for new virtual machines; default = 1024')

        parser.add_option('-d',
                '--distro',
                dest='distro',
                default='arch',
                help='The name of the operating system to use, butter will detect'\
                        + ' and use the latest available image; default = arch')

        parser.add_option('-e',
                '--env',
                '--environment',
                dest='env',
                default='',
                help='The puppet environment for this virtual machine to'\
                    + ' attatch to. By default this will be determined by'
                    + ' the hostname')

        parser.add_option('-a',
                '--avail',
                dest='avail',
                default=False,
                action='store_true',
                help='This flag is for the Query command, this will cause'\
                    + ' the available resources on the hypervisors to be'\
                    + ' displayed')

        parser.add_option('-f',
                '--force',
                dest='force',
                default=False,
                action='store_true',
                help='Bypass any "are you sure" questions, use with caution!')

        parser.add_option('--clear-node',
                dest='clear_node',
                default='',
                help='Specify which hypervisor to migrate all of the virtual'\
                    + ' machines off of.')

        parser.add_option('--hyper',
                '--hypervisor',
                dest='hyper',
                default='',
                help='The explicit name of the hypervisor to use, bypass node'\
                    + ' detection by butter')


        parser.add_option('--config',
                dest='config',
                default='/etc/butter/kvm.conf')

        options, args = parser.parse_args()

        cli = {}

        cli['create'] = options.create
        cli['destroy'] = options.destroy
        cli['purge'] = options.purge
        cli['query'] = options.query
        cli['migrate'] = options.migrate
        cli['reset'] = options.reset
        cli['name'] = options.name
        cli['distro'] = options.distro
        cli['root'] = options.root
        cli['hyper'] = options.hyper
        cli['cpus'] = options.cpus
        cli['mem'] = options.mem
        cli['avail'] = options.avail
        cli['force'] = options.force
        cli['clear_node'] = options.clear_node
        cli['config'] = options.config

        # Figure out the fqdn
        dom = domain()
        host = args[-1]
        if host.endswith(dom):
            cli['fqdn'] = host
        else:
            cli['fqdn'] = host + '.' + dom
        # Figure out the pins
        if options.pin:
            disks = []
            letters = butter.utils.gen_letters()
            for disk in options.pin.split(':'):
                comps = disk.split(',')
                disks.append({'vd' + letters[len(disks) + 1] + '.' + comps[1]),
                              'size': comps[0],
                              'format': comps[1],
                              'filesystem': comps[2]})
            cli['pin'] = disks
        else:
            cli['pin'] = ''
        # evaluate the environment
        if options.env:
            cli['env'] = options.env
        else:
            if cli['fqdn'].count('_'):
                cli['env'] = cli['fqdn'].split('_')[1].split('.')[0]
            else:
                cli['env'] = cli['fqdn'].split('.')[1]

        return cli

