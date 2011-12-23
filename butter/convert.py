#!/usr/bin/python2
'''
'''

def to_seconds(time_dict):
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

