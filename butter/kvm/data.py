'''
This module is used to gather the live state data used by butter via salt
'''
# Import salt client
import salt.client

class HVStat(object):
    '''
    Detects information about the hypervisors
    '''
    def __init__(self, opts):
        self.opts = opts
        self.local = salt.client.LocalClient()
        self.hypers = self.__hypers()
        self.resources = self.get_resources()

    def __hypers(self):
        '''
        Return a list, suitable for the salt client, of the hypervisors
        '''
        data = self.local.cmd('*', 'virt.is_kvm_hyper', timeout=3)
        hypers = set()
        for hyper in data:
            if data[hyper] == True:
                hypers.add(hyper)
        return list(hypers)

    def __refresh_resources(self):
        '''
        Sometimes the state data needs to be refreshed mid opperation, this is
        the private method to do so
        '''
        self.resources = self.get_resources()

    def get_resources(self):
        '''
        Return the full resources information about the cloud
        '''
        return self.local.cmd(self.hypers,
                'butterkvm.full_butter_data',
                arg=[self.opts['local_path']],
                expr_form='list')

    def refresh_resources(self):
        '''
        Call salt to refresh the stored state data about hypervisors
        '''
        self.__refresh_resources()

    def migration_data(self, name, hyper=''):
        '''
        Parse over the resources data to retrieve the migration information,
        pass the name of a vm to get migration data for, and an optional
        hypervisor to send the vm to.
        '''
        m_data = {}
        for host in self.resources:
            if self.resources[host]['vm_info'].has_key(name):
                m_data['from'] = host
        if not hyper:
            best = (-10000, -1000000, 1000000)
            for host in self.resources:
                if self.resources[host]['node_info']['cpus'] > best[0]:
                    if self.resources[host]['freemem'] > best[1]:
                        if len(self.resources[host]['vm_info']) < best[2]:
                            best = (self.resources[host]['node_info']['cpus'],
                                    self.resources[host]['freemem'],
                                    len(self.resources[host]['vm_info']))
                            m_data['to'] = host
        else:
            if self.resources.has_key(hyper):
                m_data['to'] = hyper
            else:
                return {}
        if not m_data.has_key('to') and not m_data.has_key('from'):
            return {}
        return m_data

    def print_system(self, system):
        '''
        Prints out the data to a console about a specific system
        '''
        out = 'Butter kvm query\n'
        for host in self.resources:
            if host == system:
                out += 'Information for ' + host + ' -\n'
                out += '    Available cpus: '\
                    + str(self.resources[host]['freecpu']) + '\n'
                out += '    Free Memory: '\
                    + str(self.resources[host]['freemem']) + '\n'
                out += '    Local Images: '\
                    + str(self.resources[host]['local_images']) + '\n'
                out += '    Total cpu cores: '\
                    + str(self.resources[host]['node_info']['cpus']) + '\n'
                out += '    Total Memory: '\
                    + str(self.resources[host]['node_info']['phymemory']) + '\n'
                out += '  Virtual machines running on ' + host + ' -\n'
                for name, info in self.resources[host]['vm_info'].items():
                    out += '      ' + name + ' -\n'
                    out += '        Virtual CPUS: ' + str(info['cpu']) + '\n'
                    out += '        Virtual Memory: ' + str(info['mem']) + '\n'
                    out += '        State: ' + info['state'] + '\n'
                    out += '        Graphics: ' + info['graphics']['type']\
                        +  ' - ' + host + ':' + info['graphics']['port'] + '\n'
                    out += '        Disks:\n'
                    for dev, path in info['disks'].items():
                        out += '          ' + dev + ': ' + path + '\n'
            elif self.resources[host]['vm_info'].has_key(system):
                out += 'Virtual machine running on host ' + host + '\n'
                name = system
                info = self.resources[host]['vm_info'][system]
                out += '      ' + name + ' -\n'
                out += '        Virtual CPUS: ' + str(info['cpu']) + '\n'
                out += '        Virtual Memory: ' + str(info['mem']) + '\n'
                out += '        State: ' + info['state'] + '\n'
                out += '        Graphics: ' + info['graphics']['type']\
                    +  ' - ' + host + ':' + info['graphics']['port'] + '\n'
                out += '        Disks:\n'
                for dev, path in info['disks'].items():
                    out += '          ' + dev + ': ' + path + '\n'
        print out

    def print_query(self):
        '''
        Prints out the information gathered in a clean way
        '''
        out = 'Butter kvm query\n'
        for host in self.resources:
            out += 'Information for ' + host + ' -\n'
            out += '    Available cpus: '\
                + str(self.resources[host]['freecpu']) + '\n'
            out += '    Free Memory: '\
                + str(self.resources[host]['freemem']) + '\n'
            out += '    Local Images: '\
                + str(self.resources[host]['local_images']) + '\n'
            out += '    Total cpu cores: '\
                + str(self.resources[host]['node_info']['cpus']) + '\n'
            out += '    Total Memory: '\
                + str(self.resources[host]['node_info']['phymemory']) + '\n'
            out += '  Virtual machines running on ' + host + ' -\n'
            for name, info in self.resources[host]['vm_info'].items():
                out += '      ' + name + ' -\n'
                out += '        Virtual CPUS: ' + str(info['cpu']) + '\n'
                out += '        Virtual Memory: ' + str(info['mem']) + '\n'
                out += '        State: ' + info['state'] + '\n'
                out += '        Graphics: ' + info['graphics']['type']\
                    +  ' - ' + host + ':' + info['graphics']['port'] + '\n'
                out += '        Disks:\n'
                for dev, path in info['disks'].items():
                    out += '          ' + dev + ': ' + path + '\n'
        print out
