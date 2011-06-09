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
           }

def mine(frame, ids):
    '''
    Read out the data for the passed ids in the mongo database
    '''
    data = {}
    comm = pymongo.Connection(
            __opts__['mongo.host'],
            __opts__['mongo.port'],
            )
    db = conn[__opts__]['mongo.db']
    
