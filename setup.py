#!/usr/bin/python2
'''
The setup script for butter
'''

from butter.version import PACKAGE, VERSION, URL
from distutils.core import setup

setup(name=PACKAGE,
      version=VERSION,
      description='High level execution manager',
      author='Thomas S Hatch',
      author_email='thatch45@gmail.com',
      url=URL,
      packages=[
                'butter',
                'butter.kvm',
                'butter.kvmd',
                'butter.vmcache',
                ],
      scripts=[
               'scripts/butter',
              ],
      data_files=[('/etc/butter',
                    [
                     'conf/kvm',
                     'conf/kvmd',
                     'conf/vmcache.conf',
                    ]),
                  ('/etc/rc.d',
                    [
                     'init/butter-kvmd',
                     'init/butter-vmcache',
                    ]),
                 ],

     )
