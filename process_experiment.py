#!/usr/bin/env python

import sys
import os
import shutil
import errno
import datetime as dt

import file_io
import analyze
import plot


def datestamp(time=True):
    """
    Return a datestamp string in format yyyymmddTHHMMSS by default.
    If time = False, format is yyyymmdd.
    """
    if time:
        fmt = '%Y%m%dT%H%M%S'
    else:
        fmt = '%Y%m%d'
    return dt.datetime.strftime(dt.datetime.now(), fmt)


def main():
    # Command line args are in sys.argv[1], sys.argv[2] ..
    # sys.argv[0] is the script name itself and can be ignored
    config = ''
    key = ''
    if len(sys.argv) == 2:
        directory = os.path.dirname(os.path.realpath(__file__))
        config = os.path.join(directory, 'config.ini')
        key = sys.argv[1]
    elif len(sys.argv) > 2:
        config = sys.argv[1]
        key = sys.argv[2]
    else:
        print """
        usage: python process_experiment.py [config_file] key_file

        To process trikinetics experimental data, pass a config file (containing
        relatively constant parameters) and a key file (containing both parameters
        relevant to the specific experiment as well as the genotypes and
        monitor/channel positions of flies).  If only one argument is passed, the
        default configuration is used.

        When called, these files are parsed and the raw experimental data is
        processed/aggregated into two dictionaries:
        activity_dict - a table containing the raw beam crossing events, per minute
        sleep_dict    - a table where minutes of sleep are marked with a '1'
                    (sleep is defined as 5+ consecutive minutes of 0 activity)

        After the construction of these dictionaries, plots are produced for the
        experimental metadata as well as sleep and activity for each line vs all
        controls.  Other plot types are included in the plot.y module, but not
        implemented in this script.

        The activity and sleep dictionaries are written as .xls files for later use.
        """

    # read the configuration file
    config_dict = file_io.read_config(config)

    # read the key file
    (protocol_dict, genotype_dict) = file_io.read_key(key)

    # create dataframe for DEnM data
    DEnM_df = file_io.read_DEnM_data(protocol_dict['DEnM'], config_dict['env_monitors'])

    # since loading activity monitor data is expensive, find out which
    # monitors we need first, then load the data into DAM_dict
    dam_monitors = set(item[0] for sublist in genotype_dict.itervalues() for item in sublist)
    DAM_dict = {'M' + str(monitor): file_io.read_DAM_data(monitor, config_dict['max_monitor']) for monitor in dam_monitors}

    # sort/collect data by genotype and create activity dict
    activity_dict = analyze.aggregate_by_genotype(genotype_dict, config_dict, DEnM_df, DAM_dict)
    # mark and remove dead fly data so that it isn't plotted
    dead_flies = analyze.mark_dead_flies(protocol_dict, DEnM_df, activity_dict, genotype_dict)
    dead_flies_filename = key[:-4] + '_dead_flies' + '.txt'
    with open(dead_flies_filename, "a") as myfile:
        myfile.write('\n'.join(dead_flies))
    # create sleep dict from activity dict
    sleep_dict = analyze.calculate_sleep(activity_dict)

    # create subfolder for output
    f = key[:-4] + '_plots'
    try:
        os.makedirs(f)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise
    shutil.copy(key, f) # copy key file to output folder
    shutil.move(dead_flies_filename, f) # move dead_flies file to output folder
    os.chdir(f) # move into the output folder, so all subsequent files will be saved there

    # plot the DEnM data, including light intensity, temperature, and relative humidity
    plot.metadata(protocol_dict, DEnM_df)

    # plot the activity and sleep of each genotype individually, with all controls
    controls = list()
    if set(protocol_dict['control_genotype']) & set(genotype_dict.keys()):
        controls = protocol_dict['control_genotype']
    for genotype in genotype_dict.keys():
        if genotype not in protocol_dict['control_genotype']:
            genotype_list = list(controls)
            genotype_list.append(genotype)
            plot.data(protocol_dict, DEnM_df, activity_dict, genotype_list, 'activity')
            plot.data(protocol_dict, DEnM_df, sleep_dict, genotype_list, 'sleep')

    # write the data to excel files
    file_io.write_data(protocol_dict, DEnM_df, activity_dict, key[:-4] + '_activity.xls')
    file_io.write_data(protocol_dict, DEnM_df, sleep_dict, key[:-4] + '_sleep.xls')

# Standard boilerplate to call the main() function to begin
# the program.
if __name__ == '__main__':
    main()
