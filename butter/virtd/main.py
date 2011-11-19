#!/usr/bin/python2
'''
'''
from .config import load_config
import argparse
import logging
import os
import re
import sys

log = logging.getLogger(__name__)

def _list(args):
    '''
    List images.
    '''
    print "XXX LIST",args

def _start(args):
    '''
    Start virtd daemon.
    '''
    print "XXX START",args

def _stop(args):
    '''
    Stop virtd daemon.
    '''
    print "XXX STOP",args

def _status(args):
    '''
    Display virtd daemon status.
    '''
    print "XXX STATUS",args

def _sync(args):
    '''
    Synchronize butter's image cache with latest image on the varch server.
    '''
    print "XXX SYNC",args

def _parse(argv):
    '''
    Parse the 'butter virtd' command line.
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument('--config',
            dest='configfile',
            default='/etc/butter/virtd',
            help='An alternative butter virtd '
                 'config file; default: /etc/butter/virtd')

    subparsers = parser.add_subparsers(help='sub-command help')

    subparser  = subparsers.add_parser('list', help='list virtd objects')
    subparser.add_argument('-i',
                           dest='what',
                           action='store_const',
                           const='images',
                           help='list images')
    subparser.set_defaults(func=_list)

    subparser = subparsers.add_parser('start', help='start the virtd daemon')
    subparser.set_defaults(func=_start)

    subparser = subparsers.add_parser('stop', help='stop the virtd daemon')
    subparser.set_defaults(func=_stop)

    subparser  = subparsers.add_parser('status', help='is virtd daemon running?')
    subparser.set_defaults(func=_status)

    subparser  = subparsers.add_parser('sync', help='synchronize cache with varch server')
    subparser.set_defaults(func=_sync)

    args = parser.parse_args(argv[2:])
    args.config = load_config(args.configfile)

    # Compile the regex patterns
    for key in ['image_pattern', 'digest_pattern']:
        value = args.config.get(key)
        if not value:
            value = '.*'
        try:
            compiled = re.compile(value)
            args.config[key] = value
        except re.error, ex:
            print >> sys.stderr, 'bad regex for {}: {}' \
                                 .format(key, value)
            sys.exit(1)

    # Convert time to number of seconds
    for key in ['sync_interval', 'keep_for']:
        value = args.config.get(key)
        if not value:
            value = '0'
        try:
            new_value = _time_to_secs(value)
            args.config[key] = new_value
        except RuntimeError, ex:
            print >> sys.stderr, 'invalid number for {}: {}' \
                                 .format(key, value)
            sys.exit(1)
    return args

def _time_to_secs(time_dict):
    '''
    Convert a time dictionary into a number of seconds.
    The dictionary may contain: day, days, hour, hours, hr, hrs,
    minute, minutes, min, mins, second, seconds, sec, and secs for keys
    and either a number for a value or a string that converts into a number.
    '''
    num_secs = 0
    for unit, multiplier in [('days',    24 * 60 * 60),
                             ('day',     24 * 60 * 60),
                             ('hours',   60 * 60),
                             ('hour',    60 * 60),
                             ('hrs',     60 * 60),
                             ('hr',      60 * 60),
                             ('minutes', 60),
                             ('minute',  60),
                             ('mins',    60),
                             ('min',     60),
                             ('seconds', 1),
                             ('second',  1),
                             ('secs',    1),
                             ('sec',     1)]:
        value = time_dict.get(unit)
        if value:
            num_secs += float(value) * multiplier
    return num_secs

def main(argv):
    '''
    Execute the 'butter virtd' command.
    '''
    args = _parse(argv)
    if args.func is None:
        print >> sys.stderr, 'internal error: func is None'
        sys.exit(1)
    args.func(args)
