'''
Manage butter statd data stored in a mongo database
'''

# Import python libs
import datetime
import os
import re

# Import mongo libs
import pymongo
from pymongo import objectid

import butter.log

log = butter.log.getLogger(__name__)

__opts__ = {
            'mongo.host': 'salt',
            'mongo.port': 27017,
            'mongo.db': 'salt',
            'mongo.user': '',
            'mongo.password': '',
            'mongo.last_id.filename': '/var/cache/butter/statd/mongo.last_id',
           }

class PersistentLastObjectId(object):
    def __init__(self):
        self.pathname = None
        self.last_id = None
        self.next_id = None

    def load(self, pathname):
        '''
        Load the last examined object id.
        '''
        self.pathname = pathname
        self.tmpname  = self.pathname + '.new'
        self.next_id = None
        try:
            log.trace('load last id from %s', self.pathname)
            with open(self.pathname, 'r') as f:
                self.last_id = objectid.ObjectId(f.read().strip())
        except (OSError, IOError, pymongo.errors.InvalidId):
            epoch = datetime.datetime(1970, 1, 1)
            self.last_id = objectid.ObjectId.from_datetime(epoch)
            parent = os.path.dirname(self.pathname)
            if not os.path.isdir(parent):
                os.makedirs(parent, 0700)

    def candidate_id(self, objid):
        '''
        Remember the id if it is greater than any id seen so far.
        '''
        if not self.next_id or objid > self.next_id:
            self.next_id = objid

    def save(self):
        '''
        Save the last examined object id.
        '''
        if self.next_id and self.next_id > self.last_id:
            self.last_id = self.next_id
            log.trace('save statd last_id %s to %s',
                        self.last_id, self.pathname)
            try:
                with open(self.tmpname, 'w') as f:
                    f.write(str(_last_id))
                    f.write('\n')
                os.rename(self.tmpname, self.pathname)
            except (OSError, IOError), ex:
                log.error("can't save statd last_id to %s: %s",
                          _last_filename, ex, exc_info=ex)

_last_id = PersistentLastObjectId()

def mine(frame, ids):
    '''
    Read out the data for the passed ids in the mongo database, frame
    is the number of returns to grab per host

    returns the generic data for butter statd:
    {'minion_id': {jid: data, {jid: data}, ...}
    '''
    if _last_id.pathname is None:
        _last_id.load(__opts__['mongo.last_id.filename'])

    # Set up the return
    ret = {}
    # Compile the regex
    pat = re.compile(ids)
    # Connect to mongo
    conn = pymongo.Connection(
            __opts__['mongo.host'],
            __opts__['mongo.port'],
            )
    db = conn[__opts__['mongo.db']]
    user = __opts__['mongo.user']
    password = __opts__['mongo.password']
    if user and password:
        db.authenticate(user, password)
    
    # Iterate over collections (hosts)
    next_id = _last_id
    criteria = {'_id' : {'$gt' : _last_id.last_id}}
    for name in db.collection_names():
        if pat.match(name) and not name.startswith('system.'):
            # We have a host to add to ret
            log.trace('search %s for _id > %s', name, _last_id.last_id)
            ret[name] = {}
            for obj in db[name].find(criteria).sort('_id', -1).limit(frame):
                for key, item in obj.items():
                    if key == '_id':
                        _last_id.candidate_id(item)
                    else:
                        ret[name][key] = item
    _last_id.save()
    return ret
