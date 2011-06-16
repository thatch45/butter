#!/usr/bin/python2
'''
The setup script for butter
'''

from distutils.core import setup

setup(name='butter',
      version='0.4.0',
      description='High level execution manager',
      author='Thomas S Hatch',
      author_email='thatch45@gmail.com',
      url='https://github.com/thatch45/butter',
      packages=[
                'butter',
                'butter.kvm',
                'butter.kvmd',
                'butter.statd',
                'butter.statd.data',
                'butter.statd.alert',
                ],
      scripts=[
               'scripts/butter',
              ],
      data_files=[('/etc/butter',
                    [
                     'conf/kvm',
                     'conf/kvmd',
                     'conf/statd',
                    ]),
                  ('/etc/rc.d',
                    [
                     'init/butter-kvmd',
                    ]),
                 ],

     )
