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
        data = self.local.cmd('*', 'virt.is_kvm_hyper')
        hypers = set()
        for hyper in data:
            if data[hyper] == True:
                hypers.add(hyper)
        return list(hypers)

    def get_resources(self):
        '''
        Return the full resources information about the cloud
        '''
        return self.local.cmd(self.hypers,
                'butterkvm.full_butter_data',
                arg=[self.opts['local_path']],
                expr_form='list')

    def system(self, system):
        '''
        Returns the data pertinant to a specific system
        '''
        return system

    def print_system(self, system):
        '''
        Prints out the data to a console about a specific system
        '''
        print self.system(system)

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
                out += '      ' + name + ' :\n'
                out += '        Virtual CPUS: ' + str(info['cpu']) + '\n'
                out += '        Virtual Memory: ' + str(info['mem']) + '\n'
                out += '        State: ' + info['state'] + '\n'
                out += '        Graphics: ' + info['graphics']['type']\
                    +  ' - ' + host + ':' + info['graphics']['port'] + '\n'
                out += '        Disks:\n'
                for dev, path in info['disks'].items():
                    out += '          ' + dev + ': ' + path + '\n'
        print out
