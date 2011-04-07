'''
The create.py module is used to provision fresh virtual machines, if needed the
create.py module creates the needed filesystem higherarchy, coppied the files
into place, generates the libvirt xml configuration, and starts the virtual
machine.
'''

# Import butter libs
import butter.kvm.data
import butter.utils
import butter.kvm.overlay
# Import python libs
import shutil
import os
import subprocess

def find_image(pool, distro):
    '''
    Returns the image to move into the final location.
    '''
    fn_types = ['Qemu',
                'data',
                'x86',
                ]
    images = []
    if not os.path.isdir(pool):
        raise Exception('The virtual machine image pool dir is not present')
    for fn_ in os.listdir(pool):
        path = os.path.join(pool, fn_)
        f_cmd = 'file ' + path
        f_type = subprocess.Popen(f_cmd,
            shell=True,
            stdout=subprocess.PIPE).communicate()[0]
        f_type = f_type.split(':')[1].split()[0]
        if not fn_types.count(f_type):
            continue
        if os.path.isdir(path):
            continue
        if fn_.split('_')[0] == distro:
            images.append(fn_)
    images.sort()
    if not images:
        raise Exception('No images found matching the specified distro')
    return os.path.join(pool, images[-1])
        

class Create(object):
    '''
    Manages the creation of virtual machines
    '''
    def __init__(self, opts, hvstat):
        self.opts = opts
        self.instance = self.__gen_instance()
        self.hvstat = hvstat
        self.local = self.hvstat.local
        self.over = butter.kvm.overlay.Overlay(self.opts)

    def __gen_instance(self):
        '''
        Figures out what the instance directory should be and returns it.
        '''
        instance = os.path.join(self.opts['instances'], self.opts['fqdn'])
        if not os.path.isdir(instance):
            os.makedirs(instance)
        return instance

    def __gen_xml(self, vda, conf):
        '''
        Generates the libvirt xml file for kvm
        '''
        # Don't generate the libvirt config if it already exists
        if os.path.exists(conf):
            return

        data = '''
<domain type='kvm'>
        <name>%%NAME%%</name>
        <vcpu>%%CPU%%</vcpu>
        <memory>%%MEM%%</memory>
        <os>
                <type>hvm</type>
                <boot dev='hd'/>
        </os>
        <devices>
                <emulator>/usr/bin/kvm</emulator>
                <disk type='file' device='disk'>
                        <source file='%%VDA%%'/>
                        <target dev='vda' bus='virtio'/>
                        <driver name='qemu' cache='writeback' io='native'/>
                </disk>
                %%PIN%%
                %%NICS%%
                <graphics type='vnc' listen='0.0.0.0' autoport='yes'/>
        </devices>
        <features>
                <acpi/>
        </features>
</domain>
        '''
        data = data.replace('%%NAME%%', self.opts['fqdn'])
        data = data.replace('%%CPU%%', str(self.opts['cpus']))
        data = data.replace('%%MEM%%', str(self.opts['mem'] * 1024))
        data = data.replace('%%VDA%%', vda)
        nics = ''
        for bridge in self.opts['network']:
            nic = '''
                <interface type='bridge'>
                        <source bridge='%%BRIDGE%%'/>
                        <mac address='%%MAC%%'/>
                        <model type='virtio'/>
                </interface>\n'''
            nic = nic.replace('%%BRIDGE%%', bridge)
            nic = nic.replace('%%MAC%%',
                    self.over.macs[self.opts['network'][bridge]])
            nics += nic
        data = data.replace('%%NICS%%', nics)

        if self.opts['pin']:
            letters = butter.utils.gen_letters()
            pin_str = ''
            for ind in range(0, len(self.opts['pin'])):
                disk = self.opts['pin'][ind]
                pin_d = '''
                <disk type='file' device='disk'>
                        <source file='%%PIN_PATH%%'/>
                        <target dev='%%VD%%' bus='virtio'/>
                        <driver name='qemu' type='%%TYPE%%' cache='writeback' io='native'/>
                </disk>
                '''

                pin_d = pin_d.replace('%%PIN_PATH%%', disk['path'])
                pin_d = pin_d.replace('%%TYPE%%', disk['format'])
                pin_d = pin_d.replace('%%VD%%', 'vd' + letters[ind + 1])

                pin_str += pin_d
            data = data.replace('%%PIN%%', pin_str)
        else:
            data = data.replace('%%PIN%%', '')
        open(conf, 'w+').write(data)

    def _apply_overlay(self, host, vda):
        '''
        Calls the hypervisor to apply the overlay
        '''
        return self.local.cmd(host,
                              'butterkvm.apply_overlay',
                              [vda, self.instance],
                              120)

    def _find_hyper(self):
        '''
        Returns the hypervisor to create the vm on
        Returns:
        dict {'hyper': '<hypervisor>',
              'state': <bool>}
        '''
        ret = {'hyper': '',
               'state': False}
        best = (-10000, -1000000, 1000000)
        resources = self.hvstat.resources
        # Is the vm running somewhere?
        for host in resources:
            for vm_ in resources[host]['vm_info']:
                if self.opts['fqdn'] == vm_:
                    # The vm already exists in the cloud
                    ret['hyper'] = host
                    ret['state'] = True
                    return ret

        # Is the vm installed to a local path somewhere?
        hosts = set()
        for host in resources:
            if resources[host]['local_images'].count(self.opts['fqdn']):
                hosts.add(host)
        if len(hosts) > 1:
            ret['hyper'] = hosts
            return ret
        elif len(hosts) == 1:
            ret['hyper'] = hosts.pop()
            return ret

        # Is the hypervisor defined on the command line?
        if self.opts['hyper'] and resources.has_key(self.opts['hyper']):
            ret['hyper'] = self.opts['hyper']
            ret['state'] = False
            return ret
        elif self.opts['hyper'] and not resources.has_key(self.opts['hyper']):
            # hyper specified on the command line does not exist
            ret['hyper'] = self.opts['hyper']
            ret['state'] = True
            return ret
        
        # The vm destination needs to be discovered
        for host in resources:
            if resources[host]['node_info']['cpus'] > best[0]:
                if resources[host]['freemem'] > best[1]:
                    if len(resources[host]['vm_info']) < best[2]:
                        best = (resources[host]['node_info']['cpus'],
                                resources[host]['freemem'],
                                len(resources[host]['vm_info']))
                        ret['hyper'] = host
        return ret

    def create(self):
        '''
        Create a new virtual machine, returns the hypervisor housing the
        virtual machine.
        Return a dict describing the action taken
        
        {'hyper': '<hypervisor(s) of the system in question>',
         'state': 
            'running' - The virtual machine is already running in the cloud |
            'multiple' - The virtual machine is down, and there are multiple
                matching disk images in the cloud |
            'started' - The vm already existed, butter started the vm |
            'created' - The vm was freshly created}
        '''
        h_data = self._find_hyper()
        if type(h_data['hyper']) == type(set()):
            return {'hyper': h_data['hyper'], 'state': 'multiple'}
        if h_data['state']:
            return {'hyper': h_data['hyper'], 'state': 'running'}
        # Double check the instace dir
        if not os.path.isdir(self.instance):
            os.makedirs(self.instance)
        # Get the root image
        image = find_image(self.opts['images'], self.opts['distro'])
        # Execute the logic to figure out where the root image needs to be
        vda = os.path.join(self.opts['local_path'], self.opts['fqdn'], 'vda')
        # Place the xml file
        conf = os.path.join(self.instance, 'config.xml')
        self.__gen_xml(vda, conf)
        # Generate and apply the overlay
        self.over.setup_overlay()
        # Pass it over to the hypervisor
        self.local.cmd(h_data['hyper'], 'butterkvm.create',
            [
            self.instance,
            vda,
            image,
            self.opts['pin'],
            ],
            timeout=240,
            )
        # Verify that the vm was created
        self.hvstat.refresh_resources()
        created = self.hvstat.find_vm(self.opts['fqdn'])
        if not created:
            print 'Failed to create the virtual machine'
            return False
        print 'Virtual machine ' + self.opts['fqdn'] + ' created on '\
                + created + '.'
        return True

    def destroy(self):
        '''
        Force quit the named vm
        '''
        host = self.find_host()
        if not host:
            print 'Virtual machine ' + self.opts['fqdn'] + ' not found in'\
                + ' the cloud'
            return False
        return self.local.cmd(host, 'virt.destroy', [self.opts['fqdn']])

    def purge(self):
        '''
        Destroy and DELETE the named vm
        '''
        host = self.find_host()
        if not host:
            print 'Virtual machine ' + self.opts['fqdn'] + ' not found in'\
                + ' the cloud'
            return False
        if not self.opts['force']:
            print 'This action will recursively destroy a virtual machine, you'\
                + ' better be darn sure you know what you are doing!!'
            conf = raw_input('Please enter yes or no [yes/No]: ')
            if not conf.strip() == 'yes':
                return
        if type(host) == type(set()):
            self.local.cmd(list(host),
                    'virt.purge',
                    [self.opts['fqdn'], True],
                    expr_form='list')
        else:
            self.local.cmd(host, 'virt.purge', [self.opts['fqdn'], True])
        if os.path.isdir(self.instance):
            shutil.rmtree(self.instance)

    def find_host(self):
        '''
        Returns the hostname of the hypervisor housing the named vm
        '''
        h_data = self._find_hyper()
        if h_data['state']:
            return h_data['hyper']
        else:
            return None

