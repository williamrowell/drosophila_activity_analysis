'''
Created on Mar 6, 2014

@author: rowellw

Some functions that aren't yet used, but may be in the future
'''


def bad_status(df, first, last):
    '''
    Check the status column of df between indices first and last for any
     values that aren't 24 or 1.
    '''
    first_time = dt.datetime.strptime(first, '%Y%m%dT%H%M%S')
    last_time = dt.datetime.strptime(last, '%Y%m%dT%H%M%S')

    status = set(df.ix[first_time:last_time].status.values)
    status.discard(1)
    status.discard(24)

    return not status

def datestamp(time=True):
    '''
    Return a datestamp string in format yyyymmddTHHMMSS by default.
    If time = False, format is yyyymmdd.
    '''
    if time: fmt = '%Y%m%dT%H%M%S'
    else: fmt = '%Y%m%d'
    return dt.datetime.strftime(dt.datetime.now(), fmt)
