'''
Initialize command line stacks and direct them into the correct subsystem
'''
import sys
import butter.kvm
import butter.kvmd
import butter.statd

subsys = [
        'kvm',
        'kvmd',
        'statd',
        ]

def __run_kvm():
    '''
    Parse the butter command line for kvm commands and run the logic
    '''
    kvm = butter.kvm.KVM()
    kvm.run()

def __run_kvmd():
    '''
    Parse the butter command line for kvmd commands and execute the kvm daemon
    '''
    kvmd = butter.kvmd.KVMD()
    kvmd.run()

def __run_statd():
    '''
    Parse the statd command line and kick off the butter statd daemon
    '''
    statd = butter.statd.StatD()
    statd.run()

def run():
    '''
    Execute the body of the butter command
    '''
    dia = '''
Welcome to the butter toolkit, butter is the objective execution and management
layer built on top of the Salt communication framework.

To access the butter help system execute a butter subsytem's --help call:
    # butter kvm --help

The available subsystems are:'''
    if len(sys.argv) == 1:

        print dia
        print subsys
        sys.exit(42)
    elif not subsys.count(sys.argv[1]):
        print dia
        print subsys
        sys.exit(42)

    {
    'kvm': __run_kvm,
    'kvmd': __run_kvmd,
    'statd': __run_statd,
    }[sys.argv[1]]()
