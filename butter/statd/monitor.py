'''
Reads the data returned from the gather system and executes any alerts
'''
# Import Python Libs
import datetime
import logging
import sys
import time

# Import butter libs
import butter.loader

log = logging.getLogger(__name__)

class Monitor(object):
    '''
    This class manages a loop that watches changes in a statd data backend
    '''
    def __init__(self, opts):
        self.opts = opts
        self.data = butter.loader.statd_data(self.opts)
        self.alerters = butter.loader.statd_alert(self.opts)
        self.mine = self.__get_miner()

    def __get_miner(self):
        '''
        Return the function used to mine data
        '''
        name = '{0[data_backend]}_data.mine'.format(self.opts)
        if self.data.has_key(name):
            return self.data[name]
        err = 'Data backend for {0[data_backend]} was not found, ' + \
              'check the "data_backend" configuration value.'
        err.format(self.opts)
        sys.stderr.write(err)
        sys.exit(2)

    def fresh_data(self):
        '''
        Return the data set as it is configured
        '''
        return self.mine(self.opts['sampling_frame'], self.opts['target'])

    def gen_alerts(self, fresh):
        '''
        Itterate over fresh data and call alert functions if they are
        flagged.
        '''
        # Alerts structure:
        # {<minion id>:
        #   {<call.elem>: 
        #       {alerter: <alerter list>,
        #        type: over/under,
        #        val: server value,
        #        thresh: config value,
        #       },...
        #   },...
        # }
        now = datetime.datetime.strftime(
           datetime.datetime.now(),
           '%Y%m%d%H%M%S%f'
           )
        alerts = {}
        for name, top in fresh.items():
            alerts[name] = {}
            # Iterate over the hosts, check latest return
            latest = None
            for jid in sorted(top, reverse=True):
                if len(jid) == len(now):
                    latest = jid
            if not latest:
                return alerts
            # Itterate over the calls made by salt
            for call, data in top[latest].items():
                if self.opts['stats'].has_key(call):
                    for elem, val in data.items():
                        tag = '{0}.{1}'.format(call, elem)
                        alerts[name][tag] = {}
                        alerts[name][tag]['alerter'] = self.opts['alerter']
                        # Determine what alerters to use
                        if not self.opts['stats'][call].has_key(elem):
                            continue
                        conf = self.opts['stats'][call][elem]
                        if conf.has_key('alerter'):
                            # This element has a custom alerter
                            alerts[name][tag]['alerter'] = conf['alerter']
                        if conf.has_key('over'):
                            if conf['over'] < val:
                                # Add an alert for the "over" flag
                                alerts[name][tag]['type'] = 'over'
                                alerts[name][tag]['val'] = val
                                alerts[name][tag]['thresh'] = conf['over']
                        if conf.has_key('under'):
                            if conf['under'] > val:
                                # Add an alert for the "under" flag
                                alerts[name][tag]['type'] = 'under'
                                alerts[name][tag]['val'] = val
                                alerts[name][tag]['thresh'] = conf['under']
        return alerts

    def run_alerts(self, alerts):
        '''
        Pass in the alerts structure and execute the derived alerts
        '''
        for name in alerts:
            for tag, data in alerts[name].items():
                for alerter in data['alerter']:
                    self.alerters[alerter](name, tag, data)

    def run(self):
        '''
        Run a monitor daemon
        '''
        log.debug('start statd')
        while True:
            fresh = self.fresh_data()
            alerts = self.gen_alerts(fresh)
            log.trace('found %s alerts', len(alerts))
            self.run_alerts(alerts)
            time.sleep(self.opts['interval'] + 2)
