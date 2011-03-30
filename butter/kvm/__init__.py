'''
Initialize interactions with the butter kvm subsytem
'''
# Import Python libs
import optparse
import sys
import subprocess
import os
import time

# Import third party libs
import yaml

# Import butter libs
import butter.kvm.config
import butter.kvm.create
import butter.kvm.overlay

def domain():
    '''
    Return the domain name for this system
    '''
    # This is going to need to be more robust
    return subprocess.Popen('dnsdomainname',
            shell=True,
            stdout=subprocess.PIPE).communicate()[0].strip()

class KVM(object):
    '''
    The KVM class is used to wrap the functionality of all butter kvm calls
    '''
    def __init__(self):
        '''
        Set up a KVM object
        '''
        self.opts = self.__parse()

    def __parse(self):
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
                help='The amount of ram to give the vm in mebibytes - only'\
                        + ' read for new virtual machines; default = 1024')

        parser.add_option('-d',
                '--distro',
                dest='distro',
                default='arch',
                help='The name of the operating system to use, butter will'\
                        + ' detect and use the latest available image;'\
                        + ' default = arch')

        parser.add_option('-p',
                '--pin',
                dest='pin',
                default='',
                help='This option will create a set of local "pinned" virtual'\
                    + ' machine images which will be made available to this'\
                    + ' vm. The pinned vm image will be created on the'\
                    + ' hypervisor. The pin option is a collection of options'\
                    + ' delimited by commas. The option to pass is: '\
                    + ' <image_path>::<size in GB>,<format(raw/qcow2)>,<fs(ext4/xfs)>'\
                    + ':<size in GB>,<format(raw/qcow2)>,<fs(ext4/xfs)>, etc.')

        parser.add_option('-e',
                '--env',
                '--environment',
                dest='env',
                default='',
                help='The puppet environment for this virtual machine to'\
                    + ' attatch to. By default this will be determined by'
                    + ' the hostname')

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
                default='/etc/butter/kvm.conf',
                help='Pass in an alternative path for the butter kvm'\
                    + ' configuration file; default: /etc/butter/kvm.conf')

        options, args = parser.parse_args()

        cli = {}

        cli['create'] = options.create
        cli['destroy'] = options.destroy
        cli['purge'] = options.purge
        cli['query'] = options.query
        cli['migrate'] = options.migrate
        cli['reset'] = options.reset
        cli['distro'] = options.distro
        cli['hyper'] = options.hyper
        cli['cpus'] = options.cpus
        cli['mem'] = options.mem
        cli['force'] = options.force
        cli['clear_node'] = options.clear_node
        cli['config'] = options.config

        cli.update(butter.kvm.config.config(cli['config']))

        # Figure out the fqdn
        # This needs to be refined in case a host is not passed
        # (for things like -Q)
        cli['fqdn'] = ''
        if len(args) > 1:
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
                disks.append({'path': os.path.join(cli['local_path'],
                              'vd' + letters[len(disks) + 1] + '.' + comps[1]),
                              'size': comps[0],
                              'format': comps[1],
                              'filesystem': comps[2]})
            cli['pin'] = disks
        else:
            cli['pin'] = ''
        # evaluate the environment
        if cli['fqdn']:
            if options.env:
                cli['env'] = options.env
            else:
                if cli['fqdn'].count('_'):
                    cli['env'] = cli['fqdn'].split('_')[1].split('.')[0]
                else:
                    cli['env'] = cli['fqdn'].split('.')[1]

        return cli

    def _verify_opts(self):
        '''
        Verify that the passed options include the needed information
        '''
        if not self.opts['fqdn']:
            print ' requires the name of a virtual machine'
            sys.exit(1)

    def create_obj(self):
        '''
        Return a butter.kvm Create object
        '''
        self._verify_opts()
        return butter.kvm.create.Create(self.opts,
                butter.kvm.data.HVStat(self.opts))

    def query(self):
        '''
        Execute the logic for the query options
        '''
        data = butter.kvm.data.HVStat(self.opts)
        if self.opts['fqdn']:
            data.print_system(self.opts['fqdn'])
        else:
            data.print_query()

    def run(self):
        '''
        Execute the logic required to act on the passed state data
        '''
        # Each sequence should be a function in the class so that the
        # capabilities can be manipulated in a more api centric way
        if self.opts['create']:
            # Create Sequence
            self.create_obj().create()
        elif self.opts['destroy']:
            # Destroy Sequence
            self.create_obj().destroy()
        elif self.opts['purge']:
            # Purge Sequence
            self.create_obj().purge()
            butter.kvm.overlay.Overlay(self.opts).purge_overlay()
        elif self.opts['query']:
            # Query Sequence
            self.query()
        elif self.opts['migrate']:
            # Migrate Sequence
            butter.kvm.migrate.Migrate(self.opts).run_logic()
        elif self.opts['reset']:
            create = self.create_obj()
            create.destroy()
            time.sleep(2)
            create.create()


class KVMD(object):
    '''
    The butter kvm subsystem daemon
    '''
    def __init__(self):
        self.cli = self.__parse_cli()
        self.opts = self.__parse(self.cli['config'])

    def __parse_cli(self):
        '''
        Parse the command line options passed to the butter kvm daemon
        '''
        parser = optparse.OptionParser()
        parser.add_option('-f',
                '--foreground',
                default=False,
                action='store_true',
                dest='foreground',
                help='Run the clay daemon in the foreground')

        parser.add_option('-c',
                '--config',
                default='/etc/butter/kvm.conf',
                dest='config',
                help='Pass in an alternative configuration file')

        options, args = parser.parse_args()

        return {'foreground': options.foreground,
                'config': options.config}

    def __parse(self, conf):
        '''
        Parse the clay deamon configuration file
        '''
        opts = {}

        opts['pool'] = '/srv/vm/pool'
        opts['pool_size'] = '5'
        opts['keep_old'] = '2'
        opts['interval'] = '5'
        opts['image_source'] = ''
        opts['distros'] = 'arch'
        opts['format'] = 'raw'

        if os.path.isfile(conf):
            opts.update(yaml.load(open(self.cli['config'], 'r')))

        return opts

    def daemon(self):
        '''
        Starts the buter kvm  daemon
        '''
        kvmd = butter.kvm.daemon.Daemon(self.opts)
        if not self.cli['foreground']:
            butter.utils.daemonize()
        kvmd.watch_pool()

