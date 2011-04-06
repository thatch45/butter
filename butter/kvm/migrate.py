'''
Frontend for running vm migration
'''
# import butter libs
import butter.kvm.data

# Import salt libs
import salt.client

class Migrate(object):
    '''
    Used to manage virtual machine live migration
    '''
    def __init__(self, opts):
        self.opts = opts
        self.local = salt.client.LocalClient()
        self.data = butter.kvm.data.HVStat(self.opts)

    def run_logic(self):
        '''
        Read the opts structure and determine how to execute
        '''
        if self.opts['clear_node']:
            self.clear_node()
        else:
            self.migrate()

    def migrate(self, name=''):
        '''
        Migrate a virtual machine to the specified destoination.
        '''
        if not name:
            name = self.opts['fqdn']
        disks = {}
        for hyper in self.data.resources:
            if self.data.resources[hyper]['vm_info'].has_key(name):
                disks = self.data.resources[hyper]['vm_info'][name]['disks']
        if not disks:
            return 'Failed to find specified virtual machine'
        m_data = self.data.migration_data(name, self.opts['hyper'])

        # Prepare the target hyper to have the correct block devices
        ret = self.local.cmd(m_data['to'],
                'virt.seed_non_shared_migrate',
                [disks, True])
        if not ret:
            print 'Failed to set up the migration seed on ' + m_data['to']
            return False

        # execute migration
        print 'Migrating ' + name + ' from ' + m_data['from'] + ' to '\
              + m_data['to'] + '. Be advised that some migrations can take on'\
              + ' the order of hours to complete, and butter will block,'\
              + ' waiting for completion.'

        print self.local.cmd(m_data['from'],
                'virt.migrate_non_shared',
                [name, m_data['to']],
                timeout=7200)

        print 'Finished migrating ' + name
        return True

    def clear_node(self):
        '''
        This method will migrate all of the non-pinned virtual machines off a
        node.
        '''
        if not self.opts['clear_node']:
            raise ValueError('Please specify the node to clear with'\
                + ' --clear-node=<nodename>')
        if not self.data.resources.has_key(self.opts['clean_node']):
            raise ValueError('Specified node to migrate all vms off of is'\
                + ' not present')
        for vm_ in resources[self.opts['clean_node']]['vms']:
            # Refresh the migration resources
            self.data.refresh_resources()
            self.migrate(vm_)
