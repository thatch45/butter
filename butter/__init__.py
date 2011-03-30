'''
Initialize command line stacks and direct them into the correct subsystem
'''
import sys
import butter.kvm

subsys = [
        'kvm',
        ]

def __run_kvm():
    '''
    Parse the butter command line for kvm commands
    '''
    kvm = butter.kvm.KVM()
    kvm.run()

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
    'kvm': __run_kvm(),
    }[sys.argv[1]]()
