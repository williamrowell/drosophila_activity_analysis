'''
Created on Mar 6, 2014

@author: William Rowell
'''

import os, pickle
from . import file_io, analyze, plot


class experiment:
    '''
    Usage: exp = experiment([config,] key)
    
    A trikinetics experiment is constructed using a config file (containing 
    relatively constant parameters) and a key file (containing both parameters 
    relevant to the specific experiment as well as the genotypes and 
    monitor/channel positions of flies).  If only one argument is passed, the
    default configuration is used.
    
    When called, these files are parsed and the raw experimental data is 
    processed/aggregated into two dictionaries:
    activity_dict - a table containing the raw beam crossing events, per minute
    sleep_dict    - a table where minutes of sleep are marked with a '1'
                    (sleep is defined as 5+ consecutive minutes of 0 activity)
                    
    After construction, you can produce various plots using the following
    methods:
    plot_metadata()
    plot_activity(<genotype>)
    plot_sleep(<genotype>)
    plot_activity_vs_control(<genotype>)
    plot_sleep_vs_control(<genotype>)
    plot_all()
    
    You can also save the experiment (via pickle) for later manipulation using 
    the save() method.    
    '''


    def __init__(self, *args):
        '''
        Load experiment using configuration and key passed as parameters.
        '''
        if len(args) == 1:
            directory = os.path.dirname(os.path.realpath(__file__))
            self.config = os.path.join(directory, 'config.ini')
            self.key = args[0]
        elif len(args) > 1:
            self.config = args[0]
            self.key = args[1]
        self.config_dict = self.parse_config()
        (self.protocol_dict, self.genotype_dict) = self.parse_key()
        self.DEnM_df = self.read_DEnM()
        self.DAM_dict = self.read_DAM()
        (self.activity_dict, self.sleep_dict) = self.aggregate()


    def parse_config(self):
        '''OO wrapper around read_config.'''
        return file_io.read_config(self.config)

    def parse_key(self):
        '''OO wrapper around read_key.'''
        return file_io.read_key(self.key)

    def read_DEnM(self):
        '''OO wrapper around read_DEnM_data.'''
        return file_io.read_DEnM_data(self.protocol_dict['DEnM'],
                                      self.config_dict['env_monitors'])

    def read_DAM(self):
        '''OO wrapper around read_DAM_data.'''
        # since loading activity monitor data is expensive, find out which
        # monitors we need first, then load the data
        dam_monitors = set(item[0] for sublist in self.genotype_dict.itervalues()
                               for item in sublist)
        return {'M' + str(monitor):
                file_io.read_DAM_data(monitor, self.config_dict['max_monitor'])
                for monitor in dam_monitors}

    def aggregate(self):
        '''OO wrapper around aggregation and dead fly detection.'''
        activity_dict = analyze.aggregate_by_genotype(self.genotype_dict,
                                                      self.config_dict,
                                                      self.DEnM_df,
                                                      self.DAM_dict)

        analyze.mark_dead_flies(self.protocol_dict,
                                self.DEnM_df,
                                activity_dict,
                                self.genotype_dict)

        sleep_dict = analyze.calculate_sleep(activity_dict)
        return activity_dict, sleep_dict

    def plot_metadata(self):
        '''Produce plots for DEnM data from this experiment.'''
        plot.metadata(self.protocol_dict, self.DEnM_df)

    def plot_activity(self, genotype):
        '''Produce activity plots for genotype.'''
        plot.data(self.protocol_dict,
                  self.DEnM_df,
                  self.activity_dict,
                  genotype,
                  'activity')

    def plot_sleep(self, genotype):
        '''Produce sleep plots for genotype.'''
        plot.data(self.protocol_dict,
                  self.DEnM_df,
                  self.sleep_dict,
                  genotype, 'sleep')

    def plot_activity_vs_control(self, genotype):
        '''Produce plot of activity vs control activity.'''
        plot.data_vs_control(self.protocol_dict,
                             self.DEnM_df,
                             self.activity_dict,
                             genotype, 'activity')

    def plot_sleep_vs_control(self, genotype):
        '''Produce plot of sleep vs control sleep.'''
        plot.data_vs_control(self.protocol_dict,
                             self.DEnM_df,
                             self.sleep_dict,
                             genotype, 'sleep')

    def plot_all(self):
        '''Produce all plots for this experiment.'''
        self.plot_metadata()
        for genotype in self.genotype_dict:
            self.plot_activity(genotype)
            self.plot_sleep(genotype)

    def save(self):
        '''Pickle experiment to reuse later.'''
        pickle.dump(self, open(self.key[:-4] + '.pickle', 'wb'))

    def write_data(self):
        '''Write activity and sleep data as excel.'''
        file_io.write_data(self.protocol_dict,
                           self.DEnM_df,
                           self.activity_dict,
                           'activity',
                           self.key[:-4] + '_activity.xls')
        file_io.write_data(self.protocol_dict,
                           self.DEnM_df,
                           self.sleep_dict,
                           'sleep',
                           self.key[:-4] + '_sleep.xls')

