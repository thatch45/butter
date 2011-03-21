'''
The create.py module is used to provision fresh virtual machines, if needed the
create.py module creates the needed filesystem higherarchy, coppied the files
into place, generates the libvirt xml configuration, and starts the virtual
machine.
'''

# Import butter libs
import butter.kvm.data
import butter.utils
# Import salt
import salt.client
# Import python libs
import shutil
import os
import time
import random
import subprocess
import sys

def find_image(pool, distro):
    '''
    Returns the image to move into the final location.
    '''
    fn_types = ['Qemu',
                'data',
                'x86',
                ]
    images = []
    if not os.path.isdir(pool]):
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

    def __gen_instance(self):
        '''
        Figures out what the instance directory should be and returns it.
        '''
        sec = os.path.join(self.opts['instances'], self.opts['fqdn'])
        if os.path.isdir(pri):
            return pri
        if os.path.isdir(sec):
            return sec
        return pri

    def __gen_xml(self, vda, conf):
        '''
        Generates the libvirt xml file for kvm
        '''
        external_kernel = '''
                <kernel>%%KERNEL%%</kernel>
                <initrd>%%INITRD%%</initrd>
                <cmdline>root=%%ROOT%% vga=normal</cmdline>
        '''
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
            nic= '''
                <interface type='bridge'>
                        <source bridge='%%BRIDGE%%'/>
                        <mac address='%%MAC%%'/>
                        <model type='virtio'/>
                </interface>\n'''
            nic = nic.replace('%%BRIDGE%%', bridge)
            nic = nic.replace('%%MAC%%', butter.dns.set_mac(self.opts['fqdn'],
                self.opts['network'][bridge]))
            nics += nic
        data = data.replace('%%NICS%%', nics)

        #if self.opts['extk']:
        #    data = data.replace('%%EXTK%%', external_kernel)
        #    data = data.replace('%%KERNEL%%', self.opts['kernel'])
        #    data = data.replace('%%INITRD%%', self.opts['initrd'])
        #    data = data.replace('%%ROOT%%', root)
        #else:
        #    data = data.replace('%%EXTK%%', '')

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

        # Is the hypervisor defined on the command line?
        if self.opts['hyper'] and resources.has_key(self.opts['hyper']):
            return (self.opts['hyper'], False)
        elif not resources.has_key(self.opts['hyper']):
            # hyper specified on the command line does not exist
            return [None, True]
        
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

    # Move to minion side
    def _set_overlay(self, vda, target):
        '''
        Uses guestfish to overlay files into the vm image.
        '''
        over = os.path.join(self.opts['overlay'], self.opts['name'])
        if not os.path.isdir(over):
            return
        tarball = os.path.join(self.instance,
                str(int(time.time())) + str(random.randint(10000,99999)) + '.tgz')
        cwd = os.getcwd()
        os.chdir(over)
        print 'Packaging the virtual machine overlay'
        t_cmd = 'tar czf ' + tarball + ' *'
        subprocess.call(t_cmd, shell=True)
        print 'Applying the virtual machine overlay, this will take a few'\
            + ' moments...'
        g_cmd = ''
        if os.path.isfile('/etc/debian_version'):
            os.environ['LIBGUESTFS_QEMU'] = '/opt/guest-qemu/qemu-wrap'
        if self.opts['distro'] == 'ubuntu':
            g_cmd = 'guestfish -a ' + vda + ' --mount ' + self.opts['root']\
                  + ' tgz-in ' + tarball + ' /'
        else:
            g_cmd = 'guestfish -i -a ' + vda + ' tgz-in ' + tarball + ' /'
        subprocess.call(g_cmd, shell=True)
        os.remove(tarball)

    # Move to minion side
    def _place_image(self, image, vda):
        '''
        Moves the image file from the image pool into the final destination.
        '''
        image_d = image + '.d'
        if not os.path.isdir(image_d):
            print 'No available images in the pool, copying fresh image...'
            shutil.copy(image, vda)
            return
        images = os.listdir(image_d)
        if not images:
            print 'No available images in the pool, copying fresh image...'
            shutil.copy(image, vda)
            return
        shutil.move(os.path.join(image_d, images[0]), vda)

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
        image = find_image(self.opts['pool'], self.opts['distro'])
        # Execute the logic to figure out where the root image needs to be
        vda = os.path.join(self.local_path, self.opts['fqdn'], 'vda')
        # Place the xml file
        conf = os.path.join(self.instance, 'config.xml')
        self.__gen_xml(vda, conf)
        # Generate the overlay
        self._gen_overlay()
        # Pass it over to the hypervisor
        self.local.cmd(h_data['hyper'], 'buttervm.create',
            [
            self.instance,
            vda,
            self.opts['pin'],
            ],
            )
        return True

    def destroy(self):
        '''
        Force quit the named vm
        '''
        host = self.find_host()
        if not host:
            print 'Virtual machine ' + self.opts['name'] + ' not found in'\
                + ' the cloud'
            return
        target = fc.Overlord(host)
        target.virt.destroy(self.opts['name'])
        return target

    def purge(self):
        '''
        Destroy and DELETE the named vm
        '''
        host = self.find_host()
        target = None
        if not host:
            print 'Virtual machine ' + self.opts['name'] + ' not found in'\
                + ' the cloud'
        else:
            target = fc.Overlord(host)
        if not self.opts['force']:
            print 'This action will recursively destroy a virtual machine, you'\
                + ' better be darn sure you know what you are doing!!'
            conf = raw_input('Please enter yes or no [yes/No]: ')
            if not conf.strip() == 'yes':
                return
        if target:
            target.clayvm.purge(self.opts['name'])
        if os.path.isdir(self.instance):
            shutil.rmtree(self.instance)

    def find_host(self):
        '''
        Returns the hostname of the hypervisor housing the named vm
        '''
        h_data = self._find_hyper()
        if h_data[1]:
            return h_data[0]
        else:
            return None

    def get_host_fc(self):
        '''
        Returns a func connection to the host holding the named vm.
        '''
        h_data = self._find_hyper()
        if h_data[1]:
            return fc.Overlord(h_data[0])

