'''
The butter kvm daemon code, used to watch the pool directory and set up the
automatic deployment pool of vm images.
'''

import os
import time
import shutil
import hashlib
import random
import subprocess
import socket
import cPickle as pickle

class Daemon(object):
    '''
    The daemon is used to maintain the image pool
    '''
    def __init__(self, opts):
        '''
        '''
        self.opts = opts
        self.stamp = self.__stamp_loc()

    def __stamp_loc(self):
        '''
        Sets up the stamp file location
        '''
        stamp = os.path.join(self.opts['images'], '.stamp.p')
        if not os.path.isdir(self.opts['images']):
            os.makedirs(self.opts['images'])
        return stamp

    def _check_stamp(self):
        '''
        Checks to see if the daemon stamp has been written to the pool dir and
        if this host is the controller, if not, sleep for 15 minutes and check
        again. This ensures that only one daemon is watching files at a
        time.
        '''
        wait = True
        host = socket.gethostname()
        while wait:
            t_stamp = int(time.time())
            if os.path.isfile(self.stamp):
                s_data = pickle.load(open(self.stamp, 'r'))
                if s_data['host'] == host:
                    wait = False
                if s_data['time'] + 900 < t_stamp:
                    wait = False
            else:
                wait = False
            if wait:
                time.sleep(600)

    def _set_stamp(self):
        '''
        Saves the run stamp used to ensure that daemon is only running on one
        machine for a pool dir.
        '''
        s_data = {'host': socket.gethostname(),
                  'time': int(time.time())}
        pickle.dump(s_data, open(self.stamp, 'w+'))

    def _get_image(self):
        '''
        Attempts to download a fresh vm image from central builder.
        '''
        if not self.opts['image_source']:
            return
        for distro in self.opts['distros'].split(','):
            
            base_name = distro + '_' + time.strftime('%Y%m%d') + '-1.'
            img_name = base_name + self.opts['format']
            sha_name = base_name + 'sha512sum'
            img = os.path.join(self.opts['images'], img_name)

            if not os.path.isfile(img):
                i_path = os.path.join(self.opts['image_source'], img_name)
                s_path = os.path.join(self.opts['image_source'], sha_name)
                down_d = os.path.join(self.opts['images'], 'down.d')
                if not os.path.isdir(down_d):
                    os.makedirs(down_d)
                cwd = os.getcwd()
                os.chdir(down_d)
                iw_cmd = 'wget ' + i_path
                sw_cmd = 'wget ' + s_path
                down_i = os.path.join(down_d, img_name)
                down_s = os.path.join(down_d, sha_name)
                if os.path.isfile(down_i):
                    os.remove(down_i)
                if os.path.isfile(down_s):
                    os.remove(down_s)
                subprocess.call(iw_cmd, shell=True)
                subprocess.call(sw_cmd, shell=True)
                if not os.path.isfile(down_i):
                    os.chdir(cwd)
                    continue
                if not os.path.isfile(down_s):
                    os.chdir(cwd)
                    continue
                sha_cmd = 'sha512sum ' + down_i
                local_sha = subprocess.Popen(sha_cmd,
                        stdout=subprocess.PIPE,
                        shell=True).communicate()[0].split()[0]
                remote_sha = open(down_s, 'r').readlines()[0].split()[0]
                if not local_sha == remote_sha:
                    # Download failed! Delete the files and continue, the
                    # download will be re attempted on the next itteration
                    os.remove(down_i)
                    os.remove(down_s)
                    os.chdir(cwd)
                    continue
                shutil.move(down_i, img)
                os.chdir(cwd)

    def watch_pool(self):
        '''
        Watches the images pool and initiates the coppies and deletions
        '''
        # The fn_types list is used to house file types which can be virtual
        # machine images.
        self._check_stamp()
        self._set_stamp()
        fn_types = ['Qemu',
                    'data',
                    'x86',
                    ]
        files = {}
        ready = set()
        images = {}
        while True:
            self._get_image()
            for fn_ in os.listdir(self.opts['images']):
                path = os.path.join(self.opts['images'], fn_)
                if os.path.isdir(path):
                    continue
                size = os.stat(path).st_size
                if files.has_key(path):
                    if size == files[path]:
                        ready.add(path)
                    else:
                        files[path] = size
                else:
                    files[path] = size
            for path in ready:
                f_cmd = 'file ' + path
                f_type = subprocess.Popen(f_cmd,
                    shell=True,
                    stdout=subprocess.PIPE).communicate()[0]
                f_type = f_type.split(':')[1].split()[0]
                if not fn_types.count(f_type):
                    continue
                name = os.path.basename(path)
                distro = name.split('_')[0]
                if images.has_key(distro):
                    if not images[distro].count(name):
                        images[distro].append(name)
                else:
                    images[distro] = [name]
            for distro in images:
                images[distro].sort()
                active = os.path.join(self.opts['images'],
                        images[distro][-1])
                active_d = active + '.d'
                active_t = active + '.t'
                if not os.path.isdir(active_d):
                    os.makedirs(active_d)
                if not os.path.isdir(active_t):
                    os.makedirs(active_t)
                if os.listdir(active_t):
                    for fn_ in os.listdir(active_t):
                        os.remove(os.path.join(active_t, fn_))
                while len(images[distro]) > int(self.opts['keep_old']):
                    # Need to clean up old images
                    destroy = os.path.join(self.opts['images'],
                            images[distro].pop(0))
                    destroy_d = destroy + '.d'
                    destroy_t = destroy + '.t'
                    if os.path.isfile(destroy):
                        os.remove(destroy)
                    if os.path.isdir(destroy_d):
                        shutil.rmtree(destroy_d)
                    if os.path.isdir(destroy_t):
                        shutil.rmtree(destroy_t)
                while len(os.listdir(active_d)) < int(self.opts['pool_size']):
                    dst = hashlib.md5(str(random.randint(1,
                        9999999999))).hexdigest()
                    atfn = os.path.join(active_t, dst)
                    shutil.copy(active, atfn)
                    shutil.move(atfn, os.path.join(active_d,
                        os.path.basename(atfn)))
            time.sleep(int(self.opts['interval']))


