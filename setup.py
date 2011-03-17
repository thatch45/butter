#!/usr/bin/python2
'''
The setup script for butter
'''

from distutils.core import setup

setup(name='butter',
      version='0.0.0',
      description='High level execution manager',
      author='Thomas S Hatch',
      author_email='thatch45@gmail.com',
      url='https://github.com/thatch45/butter',
      packages=['butter', 'butter.vm'],
      scripts=['scripts/butter-vm',
               'scripts/butter-vmd',
              ],
      data_files=[('/etc/butter',
                    ['conf/vm',
                    ]),
                ('/etc/rc.d/',
                    ['init/butter-vmd',
                    ]),
                 ],

     )