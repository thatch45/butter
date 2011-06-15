'''
Frontend for running vm migration
'''
# Import python libs
import os
# Import butter libs
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

    def _clean_disks(self, name, m_data):
        '''
        Check the migration data and clean out any unused disks post migration
        This method should only be called after verification that the virtual
        machine has migrated and the local data var has a fresh resource set.
        '''
        if self.opts['instances'] == self.opts['local_path']:
            # The disks are located on shared storage, do nothing and return
            return True
        # The disks are located on local storage, verify that the disks on the
        # from vm are not in use and that the correct disk directory is being
        # called, then delete the directory.
        frm = self.data.resources[m_data['from']]
        to_ = self.data.resources[m_data['to']]
        # Verify that the state of the vm on 'to' is running
        if not to_['vm_info'][name]['state'] == 'running':
            return False
        # Vm has DEFINATELY migrated and there are files on 'from' that need to
        # be cleaned up
        if frm['vm_info'].has_key(name):
            # There is a vm on from by the name of the migrated vm
            return False
        if frm['local_images'].count(name):
            # The image is here but no vm with it
            cmd = 'rm -rf ' + os.path.join(self.opts['local_path'], name)
            self.local.cmd(m_data['from'],
                    'cmd.run',
                    [cmd])
            l_images = self.local.cmd(m_data['from'],
                    'butterkvm.local_images',
                    [self.opts['local_path']])
            if l_images[m_data['from']].count(self.opts['fqdn']):
                return False
            else:
                return True
        return False

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

        self.local.cmd(m_data['from'],
                'virt.migrate_non_shared',
                [name, m_data['to']],
                timeout=7200)

        # Verify migration
        self.data.refresh_resources()
        loc = self.data.find_vm(name)
        if not loc == m_data['to']:
            # Migration failed!!
            print 'Migration appears to have failed, please check the'\
                + ' hypervisors manually'
            return False
        else:
            if not self._clean_disks(name, m_data):
                print 'Migration completed, but the disks still remain on '\
                    + m_data['from'] + ', they must be cleaned manually.'
            else:
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
