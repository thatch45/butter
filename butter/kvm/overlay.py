'''
Prepare files which are generated before deployment for the overlay.
'''
# This interface needs to be pluggable, so that external application control
# and generating overlay components can be written in seperate files

# Import python libs
import subprocess
import os
import shutil
import sys

# Import butter libs
import butter.utils

class Overlay(object):
    '''
    Manage the creation of a basic virtual machine overlay
    '''
    def __init__(self, opts):
        self.opts = opts
        self.over = self.__gen_overlay_dir()
        self.macs = self.__find_macs()

    def __gen_overlay_dir(self):
        '''
        verify that the overlay directory is present
        '''
        over = os.path.join(self.opts['instances'],
                self.opts['fqdn'],
                'overlay')
        if not os.path.isdir(over):
            os.makedirs(over)
        return over

    def __find_macs(self):
        '''
        If dnsmasq support is enabled, search dnsmasq for the macs, otherwise
        generate fresh mac addrs.
        '''
        macs = {}
        if self.opts['dnsmasq']:
            # Dnsmasq support is enabled, determine if this host has been
            # previously configured.
            dnsmasq_conf = os.path.join(self.opts['dnsmasq'],
                    self.opts['fqdn'] + '.conf')
            if os.path.isfile(dnsmasq_conf):
                for line in open(dnsmasq_conf, 'r').readlines():
                    comps = line.split(',')
                    macs[comps[1]] = comps[0][comps[0].index(':') + 1:]
                return macs
        for bridge, dev in self.opts['network'].items():
            macs[dev] = butter.utils.gen_mac()
        return macs

    def gen_udev(self):
        '''
        Generate and place the udev network configuration file
        '''
        fn_ = os.path.join(self.over, self.opts['udev'].lstrip('/'))
        lines = []
        udev = 'SUBSYSTEM=="net", ACTION=="add", DRIVERS=="?*",'\
             + ' ATTR{address}=="%%MAC%%", ATTR{dev_id}=="0x0",'\
             + ' ATTR{type}=="1", KERNEL=="eth*", NAME="%%DEV%%"\n'
        for dev, mac in self.macs.items():
            lines.append(udev.replace('%%MAC%%', mac).replace('%%DEV%%', dev))
        if not os.path.isdir(os.path.dirname(fn_)):
            os.makedirs(os.path.dirname(fn_))
        if not os.path.exists(fn_):
            open(fn_, 'w+').writelines(lines)

    def gen_puppet(self):
        '''
        Generate and place the puppet certificates.
        '''
        privkeyd = os.path.join(self.over, 'var/lib/puppet/ssl/private_keys/')
        privkey = os.path.join(privkeyd, self.opts['fqdn'] + '.pem')
        if os.path.isfile(privkey):
            return
        if not os.path.exists(privkeyd):
            os.makedirs(privkeyd)
        ca_cmd = 'puppetca --generate ' + self.opts['fqdn']\
               + ' --privatekeydir=' + self.over
        subprocess.call(ca_cmd, shell=True)
        if os.path.isfile(os.path.join(self.over, self.opts['fqdn'] + '.pem')):
            shutil.move(os.path.join(self.over, self.opts['fqdn'] + '.pem'),
                    privkeyd)
        else:
            err = 'Failed to find puppet key, was it generated properly?'
            sys.stderr.write(err + '\n')

    def set_env(self):
        '''
        Sets the environment for puppet to use in the puppet rc script and
        puppet.conf
        '''
        conf_d = os.path.join(self.over, 'etc/conf.d')
        conf_f = os.path.join(conf_d, 'puppet')
        if not os.path.exists(conf_d):
            os.makedirs(conf_d)
        puppet_d = os.path.join(self.over, 'etc/puppet')
        puppet_f = os.path.join(puppet_d, 'puppet.conf')
        if not os.path.exists(puppet_d):
            os.makedirs(puppet_d)
        if not os.path.exists(conf_f):
            line = 'PUPPETD_ARGS="--environment=' + self.opts['env'] + '"\n'
            open(conf_f, 'w+').write(line)
        if not os.path.exists(puppet_f):
            lines = [
                     '[main]\n',
                     '    logdir = /var/log/puppet\n',
                     '    rundir = /var/run/puppet\n',
                     '    ssldir = $vardir/ssl\n',
                     '    factpath=$vardir/lib/facter\n',
                     '    pluginsync=true\n',
                     '[agent]\n',
                     '    environment = ' + self.opts['env'] + '\n',
                     '    classfile = $vardir/classes.txt\n',
                     '    localconfig = $vardir/localconfig\n',
                     '    report = true\n',
                    ]
            open(puppet_f, 'w+').writelines(lines)


    def gen_ssh(self):
        '''
        Generates initial ssh keys for the host
        '''
        keydir = os.path.join(self.over, 'etc/ssh')
        if not os.path.exists(keydir):
            os.makedirs(keydir)
        keys = [os.path.join(keydir, 'ssh_host_key'),
                os.path.join(keydir, 'ssh_host_rsa_key'),
                os.path.join(keydir, 'ssh_host_dsa_key')
               ]
        cmds = ['ssh-keygen -f ' + keydir + '/ssh_host_key -t rsa1 -C '\
                    + self.opts['fqdn']  + ' -N ""',
                'ssh-keygen -f ' + keydir + '/ssh_host_rsa_key -t rsa -C '\
                    + self.opts['fqdn'] + ' -N ""',
                'ssh-keygen -f ' + keydir + '/ssh_host_dsa_key -t dsa -C '\
                    + self.opts['fqdn'] + ' -N ""',
               ]
        for cmdi in range(0, len(cmds)):
            if os.path.exists(keys[cmdi]):
                continue
            subprocess.call(cmds[cmdi], shell=True)

    def gen_dnsmasq(self):
        '''
        Generate all the DHCP configs for dnsmasq
        '''
        fn_ = os.path.join(self.opts['dnsmasq'],
                self.opts['fqdn'] + '.conf')
        if os.path.exists(fn_):
            return False
        configs = []
        for dev, mac in self.macs.items():
            if not dev.startswith('virt_'):
                dev = 'virt_' + dev
            configs.append("dhcp-host=net:%s,%s,%s,2h"%(dev,
                mac,
                self.opts['fqdn']))
        configs.append("")
        configs = os.linesep.join(configs)

        open(fn_, 'w+').writelines(configs)
        
        return True

    def setup_overlay(self):
        '''
        Run the sequence that sets up the overlay
        '''
        self.gen_ssh()
        if self.opts['puppet']:
            self.gen_puppet()
        if self.opts['dnsmasq']:
            if self.gen_dnsmasq():
                print 'Fresh dnsmasq config generated, restarting...'
                r_cmd = 'service dnsmasq restart'
                subprocess.call(r_cmd, shell=True)
        if self.opts['env']:
            self.set_env()
        if self.opts['udev']:
            self.gen_udev()

    def purge_overlay(self):
        '''
        Delete the old overlay files for a vm
        '''
        if not self.opts['force']:
            print 'This action will recursively destroy the virtual machine'\
                    + ' overlay and certificates, you better be darn sure you'\
                    + ' know what you are doing!!'
            conf = raw_input('Please enter yes or no [yes/No]: ')
            if not conf.strip() == 'yes':
                return
        if self.opts['dnsmasq']:
            dhcp = os.path.join(self.opts['dnsmasq'],
                self.opts['fqdn'] + '.conf')
            if os.path.isfile(dhcp):
                os.remove(dhcp)
        if os.path.isdir(self.over):
            shutil.rmtree(self.over)
        ca_cmd = 'puppetca --clean ' + self.opts['fqdn']
        subprocess.call(ca_cmd, shell=True)
