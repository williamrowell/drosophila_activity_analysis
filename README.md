drosophila_activity_analysis
============================

Authors: William Rowell <rowellw@janelia.hhmi.org>

This project is a collection of functions to read drosophila activity data collected by
Trikinetics *drosophila* activity and *drosophila* environmental monitors (DAMs and DEnMs),
process the activity and sleep data, and plot this data.

# FILE TYPES

There are four basic input file types: `config_file`, `key_file`, DEnM file, and DAM file:
* `config_file` is an ini file that contains global configuration values, like the numbers of known environmental monitors (DEnMs) and the highest known monitor number. An example, `config.ini`, is included.
* `key_file` is an ini file that contains experiment configuration values, like control genotypes, lights-on times, and fly positions. An example, `example_experiment.ini`, is included.
* DEnM and DAM files are as specified by [Trikinetics DAM System User Manual, Version 3.0](http://www.trikinetics.com/Downloads/DAMSystem%20User's%20Guide%203.0.pdf). (I have included the DAM System manual in the repo for reference.) The files should be named following the MonitorN.txt naming scheme, which should be the default.

# USAGE
An example script for driving these functions to analyze an experiment is included, `process_experiment.py`.
```
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

        The activity and sleep dictionaries are written as xls files for later use.
```

# MODULES
1. `file_io`: tools for reading `config_file`, `key_file`, `DEnM` files, and `DAM` files, as well as writing the processed data as `xls` files.
1. `analyze`: groups activity by genotype, marks dead flies, and calculates sleep as 5+ minutes with zero activity; resulting activity_dict and sleep_dict are dicts containing per-genotype dataframes of per-fly data.
1. `plot`: plots DEnM metadata per day and activity/sleep data per genotype per day.

# TODO
- Transform time to ZT
    - Should be as easy as subtracting lights_on
- Save per-fly data as xls
- Calculate total sleep per day aggregated
- Calculate OA mean beam counts per waking minute
- For individual flies, calculate
    1. number of sleep bouts
    1. total sleep per L, D, total
    1. sleep bout length
- Dynamically determine y limits for activity plots
- Panel plots instead of multi-page plots

# REQUIREMENTS
- python 2.7
- pandas
- numpy
- matplotlib

# NOTES
- On a PC, install Git with Git Bash from [here](https://msysgit.github.io/).  Not only will you use it to download the scripts, but you can use "Git Bash" from the context menu to open a terminal in your data folder to process the experiment.
- If you're not particularly technically saavy, I recommend grabbing Anaconda python from [here](http://continuum.io/downloads).
- It helps to make an alias in your .bashrc or .bash_profile, something like:  alias process_dam='/path/to/drosophila_activity_analysis/process_experiment.py'
- In OS X, it may be useful to enable "New Terminal Here" so that you can open a terminal easily from Finder.  Instructions can be found here:  http://stackoverflow.com/questions/420456/open-terminal-here-in-mac-os-finder\
