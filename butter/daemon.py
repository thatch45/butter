#!/usr/bin/env python

'''
Abstract UNIX daemon process.

The Daemon abstract class handles starting, stopping, and (re)configuring
a daemon process.  The class prevents running multiple instances through
the use of a /var/run/<daemon>.pid lock file.  The class intercepts SIGHUP
and sets the object's reconfigure variable.  Similiarly SIGTERM and SIGINT
set the shutdown variable.

This module will become obsolete if/when PEP 3143 (Standard daemon
process library) is added to the standard library or python-daemon
is ported to ArchLinux.

Users of this module must subclass Daemon and define the configure()
and run() methods.  See run() below for skeleton code.

See Linux Programming Interface, Michael Kerrisk, No Starch Press, 2010.
'''

import errno
import logging
import os
import signal
import sys

PID_PATHNAME = '/var/run/{name}.pid'

_log = logging.getLogger(__name__)
_daemons = []

class Daemon(object):
    '''
    '''
    def __init__(self, name):
        '''
        Initialize the daemon.
        '''
        self.name = name
        self.pidfile = PidFile(name)
        self.shutdown = False
        self.reconfigure = False

    def configure(self):
        '''
        (Re)configure the daemon.
        This method is called just before starting the daemon and
        in response to SIGHUP (i.e. kill -1).  Usually daemons will
        reread their config files and reinitialize themselved when
        this method is called.

        Returns True if the daemon was successfully configured, False otherwise

        * You should override this method.
        '''
        return True

    def run(self):
        '''
        Run the daemon.
        This method implements the actual daemon.  It is subclassed
        by the daemon author and only invoked by the start method.
        Do not invoke this from anywhere except the start method.

        By the time this method is called, the daemon will be configured,
        it will be daemonized (unless explicitly prevented), and will
        have the logger configured and connected.

        * You must override this method.
        '''
        while not self.shutdown:
            if self.reconfigure:
                self.configure()
                self.reconfigure = False

            # do work here

            # wait for more work here by:
            # 1. time.sleep() or
            # 2. select.select() with a timeout

            raise NotImplementedError()

    def start(self, run_in_foreground=False):
        '''
        Start the daemon.
        Command line interfaces should call this method to start the
        daemon running.

        If an error occurs starting the daemon, one of the following
        integers is returned.  If startup is successful, this method
        never returns.
            errno.EEXIST: the pidfile /var/run/<name>.pid exists and
                          the process it points to is running
            errno.ESRCH:  the pidfile exists but the process is
                          not running
        '''
        _log.info('starting {} daemon'.format(self.name))
        # Make sure this is the only instance running
        pid = os.getpid()
        rc = self.pidfile.create(pid)
        if rc != 0:
            return rc
        try:
            # Daemonize unless told otherwise
            if not run_in_foreground:
                daemonize()
                pid = os.getpid()
                self.pidfile.write(pid)

            _log.info('{} daemon started (pid={})'.format(self.name, pid))

            # Register signal handlers
            signal.signal(signal.SIGHUP, _handle_signals)
            signal.signal(signal.SIGTERM, _handle_signals)
            if run_in_foreground:
                signal.signal(signal.SIGINT, _handle_signals)
            _daemons.append(self)

            # Run daemon
            self.run()
        except:
            _log.critical('{} crashed'.format(self.name), exc_info=True)
        finally:
            self.pidfile.destroy()
        _log.info('{} daemon stopped'.format(self.name))
        sys.exit(0)

    def stop(self):
        '''
        Stop the daemon and delete the pid file.
        This method is not run in the daemon's process.  It sends a
        SIGTERM to the daemon process which sets the shutdown variable
        which the daemon notices and exits.
        '''
        _log.info('stopping {} daemon'.format(self.name))
        self._send_signal(signal.SIGTERM)
        self.pidfile.destroy()

    def reconfigure_daemon(self):
        '''
        Reconfigure the daemon.
        This method is not run in the daemon's process.  It sends a
        SIGHUP to the daemon process which sets the reconfigure variable
        which the daemon notices and then rereads its config file.
        '''
        _log.info('reconfiguring {} daemon'.format(self.name))
        self._send_signal(signal.SIGHUP)

    def _send_signal(self, signum):
        '''
        Send a signal to the daemon process(es).
        signum = the signal number, e.g. signal.SIG*
        '''
        pid = self.pidfile.read()
        if pid > 0:
            _log.debug('send signal {} to {}'.format(signum, pid))
            try:
                os.kill(pid, signum)
            except OSError, ex:
                if ex.errno != errno.ESRCH:
                    raise
                _log.debug('no such process: {}'.format(pid))

class PidFile(object):
    '''
    '''
    def __init__(self, daemon_name):
        '''
        Initialize the path to the pid file.
        '''
        self.path = PID_PATHNAME.format(name=daemon_name)

    def create(self, pid):
        '''
        Create the pid (lock) file.
        Returns 0 if the file was created, errno.EEXIST if the pidfile
                exists and the process is running, or errno.ESRCH if
                the pidfile exists but the process isn't running.
        '''
        try:
            _log.debug('creating lock file {}'.format(self.path))
            fd = os.open(self.path,
                         os.O_WRONLY|os.O_CREAT|os.O_EXCL,
                         0644)
            os.write(fd, '{}\n'.format(pid))
            os.close(fd)
            return 0
        except OSError, ex:
            if ex.errno == errno.EEXIST:
                if self.is_process_running():
                    _log.error('daemon already running')
                    return errno.EEXIST
                else:
                    _log.error('stale pidfile {}: no such process'
                                .format(self.path))
                    return errno.ESRCH
            else:
                _log.error('cannot create pidfile {}'.format(self.path),
                           exc_info=ex)
                raise

    def is_process_running(self):
        '''
        Is the process identified by the pid in the file still running?
        Returns True or False.
        '''
        pid = self.read()
        if pid != -1:
            try:
                os.kill(pid, 0)
                return True
            except OSError, ex:
                if ex.errno != errno.ESRCH:
                    raise
        return False

    def destroy(self):
        '''
        Delete the pid file.
        '''
        try:
            _log.debug('deleting pidfile {}'.format(self.path))
            os.remove(self.path)
        except OSError, ex:
            if ex.errno != errno.ENOENT:
                _log.debug('cannot delete pidfile {}'.format(self.path),
                            exc_info=ex)
                raise
            _log.debug('pidfile {} already deleted'.format(self.path))

    def read(self):
        '''
        Read and return the integer pid in the file.
        Returns a non-negative integer if pid can be read from file or
                -1 if an error occurs reading the file or if the file
                doesn't contain a non-negative integer.
        '''
        pid = -1
        try:
            with open(self.path, 'r') as fp:
                buf = fp.read().strip()
                _log.debug('pidfile {} contents: {}'.format(self.path, buf))
            pid = int(buf)
            if pid < 0:
                _log.error('pidfile {} contains invalid pid {}'
                            .format(self.path, buf))
                pid = -1
        except (OSError, IOError), ex:
            if ex.errno != errno.ENOENT:
                _log.error('error reading pidfile {}'.format(self.path),
                           exc_info=ex)
                raise
            _log.debug('pidfile {} does not exist'.format(self.path))
        except ValueError:
            _log.error('pidfile {} contents not an integer: {}'
                        .format(self.path, buf))
        return pid

    def write(self, pid):
        '''
        Write a new pid to the pid file.
        This method is called after a process becomes a daemon (where
        the process is forked twice and has a new pid).
        '''
        with open(self.path, 'w') as fp:
            fp.write('{}\n'.format(pid))

def daemonize():
    '''
    Daemonize the current process.
    Daemonizing a process disconnects it from the session and terminal
    that started the process so that the process isn't affected by events
    in the starting shell (e.g. logout), doesn't disrupt the starting
    shell (e.g. by printing to the terminal), and doesn't lock system
    resources (e.g. by leaving cwd on a mounted file system or holding
    open inherited file descriptors.
    Raises OSError if process partially or completely fails to daemonize.
    See Linux Programming Interface section 37.2 Creating a Daemon, p. 768
    '''
    # Ensure process isn't a process group leader
    try:
        _log.debug('daemonize: 1st fork')
        pid = os.fork()
        if pid != 0:
            _log.debug('daemonize: 1st fork parent exits')
            os._exit(0)
        _log.debug('daemonize: 1st fork child continues')
    except OSError, ex:
        _log.error('daemonize: 1st fork failed', exc_info=ex)
        raise

    # Ensure process is in its own session and has no controlling terminal
    _log.debug('daemonize: starting new session')
    os.setsid()

    # Ensure process is not session leader and can't acquire a controlling
    # terminal
    try:
        _log.debug('daemonize: 2nd fork')
        pid = os.fork()
        if pid != 0:
            _log.debug('daemonize: 2nd fork parent exits')
            os._exit(0)
        _log.debug('daemonize: 2nd fork child continues')
    except OSError, ex:
        _log.error('daemonize: 2nd fork failed', exc_info=ex)
        raise

    # Ensure files and directories are created with requested permissions
    _log.debug('daemonize: set umask to 0')
    os.umask(0)

    # Ensure process is not preventing a file system from unmounting
    _log.debug('daemonize: cd to /')
    os.chdir('/')

    # Ensure process doesn't retain open file descriptors
    _log.debug('daemonize: close file descriptors')
    for fd in _get_open_file_descriptors():
        try:
            os.close(fd)
        except OSError, ex:
            if ex.errno != errno.EBADF:
                raise

    # Ensure I/O to standard file descriptors is discarded
    _log.debug('daemonize: redirect stdin, stdout, stderr to /dev/null')
    if os.open('/dev/null', os.O_RDWR) != 0:
        raise OSError('cannot redirect stdin to /dev/null')
    os.dup2(0, 1)
    os.dup2(0, 2)

def _get_open_file_descriptors():
    '''
    Return a list of open file descriptors.
    Depending on what the system provides, this method either returns
    exactly the open file descriptors or a list of possibly open
    file descriptors.  Exclude any file descriptors used by
    non-console loggers.
    '''
    logging_fds = set()
    for handler in logging.root.handlers:
        if hasattr(handler, 'stream') and \
                hasattr(handler.stream, 'fileno') and \
                handler.stream.fileno() > 2:
            logging_fds.add(handler.stream.fileno())

    if os.path.isdir('/proc/self/fd'):
        fds = set()
        for fd in os.listdir('/proc/self/fd'):
            fds.add(int(fd))
    elif 'SC_OPEN_MAX' in os.sysconf_names:
        fds = set(range(os.sysconf('SC_OPEN_MAX')))
    else:
        fds = set(range(8192))
    return fds - logging_fds

def _handle_signals(signum, unused_frame):
    '''
    Signal handler for SIGHUP, SIGINT, and SIGTERM.
    This method only sets shutdown and reconfigure variables in the
    running daemon to avoid reentrancy errors described in
    Linux Programming Interface, section 21.2.2, pp. 422-428.
    '''
    _log.debug('handle signal {}'.format(signum))
    for daemon in _daemons:
        if signum == signal.SIGHUP:
            daemon.reconfigure = True
        elif signum == signal.SIGTERM or signum == signal.SIGINT:
            daemon.shutdown = True
