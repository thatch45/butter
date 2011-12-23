'''
Initialize command line stacks and direct them into the correct subsystem
'''
import butter.kvm
import butter.kvmd
import butter.log
import butter.vmcache
import sys

_SUBSYSTEMS = {
                'kvm':   butter.kvm.KVM,
                'kvmd':  butter.kvmd.KVMD,
                'vmcache': butter.vmcache.main.main,
             }

def _usage(argv):
    '''
    Display the usage message.
    '''
    print >> sys.stderr, '''
Welcome to the butter toolkit.  Butter is the objective execution and
management layer built on top of the Salt communication framework.

To access the help system, run 'butter <subsystem> --help'.
For example:
    # butter kvm --help

The available subsystems are: {}
'''.format(", ".join(sorted(_SUBSYSTEMS)))
    return 0

def _bad_subsystem(argv):
    '''
    Display an error message.
    '''
    print >> sys.stderr, '''error: invalid subsystem '{}'
use one of the following: {}'''.format(argv[1],
                                       ", ".join(sorted(_SUBSYSTEMS)))
    return 1

def run():
    '''
    Execute the the butter command.
    '''
    if len(sys.argv) == 1:
        handler = _usage
    else:
        handler = _SUBSYSTEMS.get(sys.argv[1], _bad_subsystem)
    butter.log.init()
    if hasattr(handler, 'run'):
        handler().run()
        rc = 0
    else:
        rc = handler(sys.argv[1:])
    sys.exit(rc)
