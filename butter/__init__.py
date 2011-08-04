'''
Initialize command line stacks and direct them into the correct subsystem
'''
import sys
import butter.kvm
import butter.kvmd
import butter.statd

_SUBSYSTEMS = {
                'kvm':   butter.kvm.KVM,
                'kvmd':  butter.kvmd.KVMD,
                'statd': butter.statd.StatD,
             }

def usage(stream):
    '''
    Display the usage message.
    '''
    print >> stream, '''
Welcome to the butter toolkit.  Butter is the objective execution and
management layer built on top of the Salt communication framework.

To access the help system, run 'butter <subsystem> --help'.
For example:
    # butter kvm --help

The available subsystems are: {}
'''.format(", ".join(sorted(_SUBSYSTEMS)))

def run():
    '''
    Execute the the butter command.
    '''
    if len(sys.argv) == 1:
        usage(sys.stdout)
        sys.exit(0)

    cls = _SUBSYSTEMS.get(sys.argv[1])
    if cls is None:
        usage(sys.stderr)
        sys.exit(1)
    cls().run()
