#!/usr/bin/python2
'''
The setup script for butter
'''

from distutils.core import setup

setup(name='butter',
      version='0.2.0',
      description='High level execution manager',
      author='Thomas S Hatch',
      author_email='thatch45@gmail.com',
      url='https://github.com/thatch45/butter',
      packages=[
                'butter',
                'butter.kvm',
                'butter.kvmd',
                'butter.statd',
                ],
      scripts=[
               'scripts/butter',
              ],
      data_files=[('/etc/butter',
                    [
                     'conf/kvm',
                     'conf/kvmd',
                    ]),
                  ('/etc/rc.d',
                    [
                     'init/butter-kvmd',
                    ]),
                 ],

     )
