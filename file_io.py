"""
Created on Mar 6, 2014

@author: William Rowell
"""

import ConfigParser
import math
import os.path
import re

import datetime as dt
import numpy as np
import pandas as pd
import analyze


def read_config(configfile):
    """
    Load program configuration information from a config-style file using
    ConfigParser.  Filename as input.
    The configuration file is where system wide configuration variables are
    stored, such as environmental monitor list or maximum monitor index.

    read_config(configfile) -> config_dict

    input configfile:   path and name for configuration file, ex. './config.ini'
    output config_dict: settings stored as key->value pairs
    """

    # does the key exist?
    assert os.path.isfile(configfile), '%s does not exist.' % configfile

    # set up the config parser
    config = ConfigParser.ConfigParser()
    config.optionxform = str  # preserves case of keys
    config.read(configfile)
    config_dict = dict()

    # The first section is a list of parameters
    options = config.options('Config')
    for option in options:
        # first try to get the option as an int
        try:
            config_dict[option] = config.getint('Config', option)
        # then try to get the option as a string
        except:
            config_dict[option] = config.get('Config', option)
    # make sure none of the options are unset
    for option in options:
        assert (config_dict[option] is not ''), \
        '%s is required, but not set.' % option

    # unpack environmental monitors into list of ints
    if type(config_dict['env_monitors']) is str:
        config_dict['env_monitors'] = [int(x.strip()) for x in config_dict['env_monitors'].split(',')]
    return config_dict


def read_key(keyfile):
    """
    Load protocol and genotype information from a config-style file
    using ConfigParser.  Filename as input.
    The key file is where experiment configuration is stored, such as which DEnm
    was used, the lights_on and lights_off times, and the genotypes.

    read_key(keyfile) -> protocol_dict

    input keyfile:        path and name for protocol file, ex. './experiment1.ini'
    output protocol_dict: protocol settings stored as key->value pairs
    """

    # does the key exist?
    assert os.path.isfile(keyfile), '%s does not exist.' % keyfile

    # set up the config parser
    config = ConfigParser.ConfigParser()
    config.optionxform = str  # preserves case of keys
    config.read(keyfile)
    protocol_dict = dict()
    genotype_dict = dict()

    # The first section is a list of parameters
    options = config.options('Protocol')
    for option in options:
        # first try to get the option as an int
        try:
            protocol_dict[option] = config.getint('Protocol', option)
        # then try to get the option as a string
        except:
            protocol_dict[option] = config.get('Protocol', option)
    # make sure none of the options are unset
    for option in options:
        assert (protocol_dict[option] is not ''), \
        '%s is required, but not set.' % option

    # check lights_on/off times and convert to datetime
    assert (0 <= protocol_dict['lights_on'] < 24), \
            'lights_on must be between 0 and 23.'
    assert (0 <= protocol_dict['lights_off'] < 24), \
            'light_off must be between 0 and 23.'
    protocol_dict['lights_on'] = dt.time(protocol_dict['lights_on'], 0, 0)
    protocol_dict['lights_off'] = dt.time(protocol_dict['lights_off'], 0, 0)

    # split the controls into a list
    protocol_dict['control_genotype'] = [x.strip() for x in protocol_dict['control_genotype'].split(',')]

    # check other protocol values
    assert (protocol_dict['DD'] >= 0), \
            'DD must be a positive integer.'
    assert (protocol_dict['check_day'] >= 0), \
            'check_day must be a positive integer.'
    assert (protocol_dict['gender'] in ['m', 'f', 'x']), \
            'gender must be one of [m,f,x].'

    # The second section is a list of genotypes and Mon/Ch positions
    # Format Mon.ChanLo-ChanHi, Mon.ChanLo-ChanHi
    genotypes = config.options('Genotypes')
    for genotype in genotypes:
        pos_string = config.get('Genotypes', genotype)
        pos_regex = re.compile(r'(\d{1,3}).(\d{1,2})-(\d{1,2})')
        # Split and store as list of 3-tuples
        # Format (Mon, ChanLo, ChanHi)
        positions = [pos_regex.match(x.strip()).groups()
                     for x in pos_string.split(',')]  # pylint: disable=E1103
        if genotype not in genotype_dict: genotype_dict[genotype] = positions
        else: genotype_dict[genotype].extend(positions)

    return protocol_dict, genotype_dict


def read_DEnM_data(monitor_number, ENV_MONITORS):
    """
    Read the Trikinetics Drosophila Environmental Monitor text file for
    'monitor_number' and return a datetime indexed df with status, Lavg,
    Tavg, Havg, and light boolean.

    read_DEnM_data(monitor_number, ENV_MONITORS) -> DEnM_df

    input monitor_number: index of the DEnM
    input ENV_MONITORS:   list of all allowed DEnMs
    output DEnM_df:       pd.dataframe of DEnM data
    """

    # test if this is an environmental monitor
    assert (int(monitor_number) in ENV_MONITORS), \
            'Monitor %s is not a known DEnM.' % str(monitor_number)

    # generate the environmental monitor datafile name
    datafile = ''.join(['Monitor', str(monitor_number), '.txt'])

    # does the file exist?
    assert os.path.isfile(datafile), \
    'DEnM data file for monitor %s does not exist.' % datafile

    # produce header names for desired rows
    columns = [1, 2, 3, 13, 18, 23]
    hr = [''] * 42
    (hr[1], hr[2], hr[3], hr[13], hr[18], hr[23]) = \
        ('date', 'time', 'status', 'Lavg', 'Tavg', 'Havg')

    # read monitor file
    df = pd.read_csv(datafile, sep='\t', header=None, names=hr, usecols=columns)

    # create datetime vector from 'date' and 'time' vectors
    df.index = [dt.datetime.strptime(df.date[i] + ' ' + df.time[i],
                                     '%d %b %y %H:%M:%S')
                for i in df.index]  # pylint: disable=E1103
    # drop 'date' and 'time' vectors
    df = df.drop('date', axis=1)
    df = df.drop('time', axis=1)

    # generate boolean light vector
    df['light'] = [True if df.Lavg[i] > 100 else False for i in df.index]

    # change temperature or humidity 0 values to NaN
    df.Tavg = df.Tavg.replace(0, np.nan)
    df.Havg = df.Havg.replace(0, np.nan)

    # correct temperature
    df.Tavg = df.Tavg.apply(lambda x: x / 10.0)
    return df


def read_DAM_data(monitor_number, MAX_MONITOR):
    """
    Read the Trikinetics Drosophila Activity Monitor text file for
    'monitor_number' and return a datetime indexed df with status,
    Lstatus, and 32 activity channels (named M#C#).

    read_DAM_data(monitor_number, MAX_MONITOR) -> DAM_df

    input monitor_number: index of the DAM
    input MAX_MONITOR:    highest allowable monitor index
    output DAM_df:        pd.dataframe of DAM data
    """

    # test if this is an activity monitor
    assert (1 <= int(monitor_number) <= MAX_MONITOR), \
            '%s is not a valid monitor number.' % str(monitor_number)

    # generate the environmental monitor datafile name
    datafile = ''.join(['Monitor', str(monitor_number), '.txt'])

    # does the file exist?
    assert os.path.isfile(datafile), \
        'DAM data file for monitor %s does not exist.' % datafile

    # produce header names for desired rows
    columns = [1, 2, 3] + range(9, 42)
    hr = [''] * 42
    (hr[1], hr[2], hr[3], hr[9]) = ('date', 'time', 'M' + str(monitor_number) +
                                    'status', 'M' + str(monitor_number) +
                                    'Lstatus')
    hr[10:42] = ['M' + str(monitor_number) + 'C' + str(i) for i in xrange(1, 33)]

    # read monitor file
    df = pd.read_csv(datafile, sep='\t', header=None, names=hr, usecols=columns)

    # create datetime vector from 'date' and 'time' vectors
    df.index = [dt.datetime.strptime(df.date[i] + ' ' + df.time[i], '%d %b %y %H:%M:%S')
                for i in df.index]  # pylint: disable=E1103
    # drop 'date' and 'time' vectors
    df = df.drop('date', axis=1)
    df = df.drop('time', axis=1)
    return df


def bad_status(df, first, last):
    '''
    Check the status column of df between indices first and last for any
    values that aren't 24 or 1.  In DAM and DEnM files, status values of
    24 indicate initialization and status values of 1 indicate "OK".
    Anything else indicates a problem of some sort.

    bad_status(df, first, last) -> status_boolean

    input df:              DAM_df or DEnM_df to check
    input first:           first index to check
    input last:            last index to check
    output status_boolean: True = bad, False = good

    '''
    first_time = dt.datetime.strptime(first, '%Y%m%dT%H%M%S')
    last_time = dt.datetime.strptime(last, '%Y%m%dT%H%M%S')

    status = set(df.ix[first_time:last_time].status.values)
    status.discard(1)
    status.discard(24)
    return not status


def write_data(protocol_dict, DEnM_df, data_dict, outname):
    """
    Write activity or sleep data to disk.

    write_data(protocol_dict, DEnM_df, data_dict, outname) -> None

    input protocol_dict: protocol settings stored as key->value pairs
    input DEnM_df:       pd.dataframe of DEnM data
    input data_dict:     activity_dict or sleep_dict
    input outname:       name to use for output file
    """

    (dates, start_date, end_date) = analyze.calculate_dates(protocol_dict, DEnM_df)

    # create string used to control binning size
    resample_freq = str(protocol_dict['bin']) + 'Min'

    # create the time series to be used for the dataframes
    t_index = DEnM_df.ix[start_date:end_date].resample(resample_freq, how='sum').index

    output_df = pd.DataFrame(index=t_index)
    output_df['date'] = [i.strftime("%Y-%m-%d") for i in output_df.index]
    output_df['time'] = [i.strftime("%H:%M:%S") for i in output_df.index]

    for genotype in data_dict:
        df = data_dict[genotype][start_date:end_date].resample(resample_freq,
                                                               how='sum')
        output_df[genotype + '_mean'] = df.mean(axis=1)
        output_df[genotype + '_sem'] = df.std(axis=1) / math.sqrt(df.shape[1])
        output_df[genotype + '_N'] = df.shape[1]
    output_df.to_excel(outname)

if __name__ == '__main__':
    pass
