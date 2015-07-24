"""
Created on Mar 6, 2014

@author: William Rowell
"""

import datetime as dt
import pandas as pd


def aggregate_by_genotype(genotype_dict, config_dict, DEnM_df, DAM_dict):
    """
    Create a dict of genotypes with a datetime indexed df for each fly.
    """

    activity = dict()
    # only collect data for which the environmental monitor status is
    # good, i.e. status isn't 51 (unreachable)
    time_series = DEnM_df.index[DEnM_df['status'] != 51]

    for genotype in genotype_dict:
        for (monitor, first, last) in genotype_dict[genotype]:
            # does the monitor make sense?
            assert (1 <= int(monitor) <= config_dict['max_monitor']), \
                '%s is not a valid monitor number.' % str(monitor)

            # do the channels make sense?
            assert (1 <= int(first) <= 32), \
                'First channel %s is out of range [1,32].' % str(first)
            assert (1 <= int(last) <= 32), \
                'Last channel %s is out of range [1,32].' % str(last)
            assert (int(first) <= int(last)), \
                'Last channel %s is less than first channel %s.' % \
                (str(last), str(first))

            # get the headers for the desired channels and append these channels
            channels = ['M' + monitor + 'C' + str(channel)
                        for channel in xrange(int(first), int(last) + 1)]
            channels_df = DAM_dict['M' + str(monitor)].ix[time_series, channels]
            if genotype not in activity:
                activity[genotype] = channels_df
            else:
                activity[genotype] = \
                    activity[genotype].join(channels_df)

    return activity


def mark_dead_flies(protocol_dict, DEnM_df, activity_dict, genotype_dict):
    """
    Given the activity_dict of dfs and a day to check, looks for
    channels for which there is no activity on check_date and deletes
    dead fly columns from the df.
    """

    # determine the index to check from check_day
    (dates, __, __) = calculate_dates(protocol_dict, DEnM_df)
    check_start = dt.datetime.combine(dates[protocol_dict['check_day']],
                                      protocol_dict['lights_on']) + \
                                      dt.timedelta(minutes=1)
    check_end = check_start + dt.timedelta(1)

    dead_flies = list()
    for genotype in activity_dict:
        for channel in activity_dict[genotype]:
            # take the set of all activity values for channel during check_date
            # if the set only contains 0, then the fly is dead
            channel_activity = set(activity_dict[genotype].ix[check_start:check_end][channel])
            channel_activity.discard(0)
            if not channel_activity:
                # we should be alerted about dead flies
                print '%s:%s - dead' % (genotype, channel)
                dead_flies.append('_'.join([genotype, channel]))
                # and the data for the dead fly should be deleted
                del activity_dict[genotype][channel]
        # if all flies of this genotype is dead, warn us and delete the df
        if activity_dict[genotype].shape[1] == 0:
            print 'All flies of genotype %s are dead.' % genotype
            del activity_dict[genotype]
            del genotype_dict[genotype]
    return dead_flies


def calculate_dates(protocol_dict, DEnM_df):
    """
    Returns a tuple of (dates, start_datetime, end_datetime) based on
    protocol_dict and datetime index of DEnM.
    """

    dates = sorted(list(set(DEnM_df.index.map(pd.Timestamp.date))))
    start_date = dt.datetime.combine(dates[1], protocol_dict['lights_on'])
    end_date = dt.datetime.combine(dates[-1], protocol_dict['lights_off'])
    return dates, start_date, end_date


def calculate_sleep(activity_dict):
    """
    Return a dict of sleep df.
    Sleep is defined as 5+ consecutive minutes without beam-crossings.
    The sleep df consists of int arrays where sleep = 1.
    """

    sleep_dict = dict()

    for genotype in activity_dict:
        df = activity_dict[genotype]

        # create a new blank df with the same index as the activity df
        sleep_dict[genotype] = pd.DataFrame(index=df.index)
        channel_length = sleep_dict[genotype].shape[0]

        # for each channel in the activity df, create a new boolean
        # column in sleep
        for channel in df:
            sleep_dict[genotype][channel] = [0] * channel_length

            # look for streaks of 5+ zeros by iterating through list
            # TODO: CHECK LOGIC ON THIS AT END OF EXPERIMENT
            i = 0
            while i < channel_length:
                # if list of 5 doesn't end with zero, next
                if ((i + 4 < channel_length) and
                    (df[channel][i + 4] != 0)):
                    i += 5
                    continue
                # if list of 5 doesn't start with zero, next 5
                if df[channel][i] != 0:
                    i += 5
                    continue
                # if list of 5 contains any non-zero values, next
                if ((i + 4 < channel_length) and
                    (df[channel][i + 1:i + 3].sum() != 0)):
                    i += 5
                    continue
                # see how far we can extend the run of zeros
                j = 4
                while ((i + j + 1 < channel_length) and
                       (df[channel][i + j + 1]) == 0):
                    j += 1
                # change runs of sleep to 1
                sleep_dict[genotype][channel][i:i + j] = 1
                # move to next beam crossing count
                i = i + j + 1
    return sleep_dict


if __name__ == '__main__':
    pass
