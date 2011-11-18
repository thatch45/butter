#!/usr/bin/python2
'''
'''
import argparse
import logging
import os

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

def main(argv):
    '''
    Parse the 'butter virtd' command line.
    '''
    parser = argparse.ArgumentParser()
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
    args.func(args)
