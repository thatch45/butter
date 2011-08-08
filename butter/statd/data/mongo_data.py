'''
Manage butter statd data stored in a mongo database
'''

# Import python libs
import re
# Import mongo libs
import pymongo

__opts__ = {
            'mongo.host': 'salt',
            'mongo.port': 27017,
            'mongo.db': 'salt',
            'mongo.user': '',
            'mongo.password': '',
           }

def mine(frame, ids):
    '''
    Read out the data for the passed ids in the mongo database, frame
    is the number of returns to grab per host

    returns the generic data for butter statd:
    {'minion_id': {jid: data, {jid: data}, ...}
    '''
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
    
    # Itterate over collections (hosts)
    for name in db.collection_names():
        if pat.match(name):
            # We have a host to add to ret
            ret[name] = {}
            for obj in db[name].find().sort('_id', -1).limit(frame):
                for key, item in obj.items():
                    if not key == '_id':
                        ret[name][key] = item
    return ret
