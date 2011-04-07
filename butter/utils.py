'''
Utilities such as logging and deamonizing
'''

# Import python modules
import sys
import os
import random

# Set up the bash output colors
BLACK = '\033[0;30m'
DARK_GRAY = '\033[1;30m'
LIGHT_GRAY = '\033[0;37m'
BLUE = '\033[0;34m'
LIGHT_BLUE = '\033[1;34m'
GREEN = '\033[0;32m'
LIGHT_GREEN = '\033[1;32m'
CYAN = '\033[0;36m'
LIGHT_CYAN = '\033[1;36m'
RED = '\033[0;31m'
LIGHT_RED = '\033[1;31m'
PURPLE = '\033[0;35m'
LIGHT_PURPLE = '\033[1;35m'
BROWN = '\033[0;33m'
YELLOW = '\033[1;33m'
WHITE = '\033[1;37m'
DEFAULT_COLOR = '\033[00m'
RED_BOLD = '\033[01;31m'
ENDC = '\033[0m'

def daemonize():
    '''
    Daemonize a process
    '''
    try: 
        pid = os.fork() 
        if pid > 0:
            # exit first parent
            sys.exit(0) 
    except OSError, e: 
        print >> sys.stderr, "fork #1 failed: %d (%s)" % (e.errno, e.strerror) 
        sys.exit(1)

    # decouple from parent environment
    os.chdir("/") 
    os.setsid() 
    os.umask(022) 

    # do second fork
    try: 
        pid = os.fork() 
        if pid > 0:
            # print "Daemon PID %d" % pid 
            sys.exit(0) 
    except OSError, e: 
        print >> sys.stderr, "fork #2 failed: %d (%s)" % (e.errno, e.strerror) 
        sys.exit(1) 

    dev_null = open('/dev/null','rw') 
    os.dup2(dev_null.fileno(), sys.stdin.fileno()) 
    os.dup2(dev_null.fileno(), sys.stdout.fileno()) 
    os.dup2(dev_null.fileno(), sys.stderr.fileno()) 

def check_root():
    '''
    Most of the clay scripts need to run as root, this function will simple
    verify that root is the user before the application discovers it.
    '''
    if os.getuid():
        print 'Sorry, clay has to run as root, it needs to opperate in a' \
                + ' privileged environment to do what it does.' \
                + ' http://xkcd.com/838/'
        sys.exit(1)

def gen_letters():
    '''
    Generate the letters used to farm out all of the virtual pin drives
    '''
    lets = map(chr, range(97, 123))
    alets = map(chr, range(97, 123))
    blets = map(chr, range(97, 123))
    for alet in alets:
        for blet in blets:
            lets.append(alet + blet)
    return lets

def gen_mac(prefix=''):
    '''
    Generates a mac addr with the defined prefix
    '''
    src = ['1','2','3','4','5','6','7','8','9','0','a','b','c','d','e','f']
    mac = prefix
    while len(mac) < 18:
        if len(mac) < 3:
            mac = random.choice(src) + random.choice(src) + ':'
        if mac.endswith(':'):
            mac += random.choice(src) + random.choice(src) + ':'
    return mac[:-1]

