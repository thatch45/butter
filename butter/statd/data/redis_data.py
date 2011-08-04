'''
Dynamic return manager for redis within statd. The primary purpose for
maintainers is to clean out old data from the returner's data store.
If a maintainer is not specified for a returner then the cleaning
is not executed, or it is assumed that another system is cleaning out
old data
'''

import redis

def clean_old(interval):
    '''
    Clear out data that is older than the configured interval from
    the data store
    '''
    pass
