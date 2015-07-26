"""
Created on Mar 6, 2014

@author: William Rowell
"""

from matplotlib.backends.backend_pdf import PdfPages
import math
import datetime as dt
import matplotlib.dates as mpld
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import analyze


COLOR_CYCLE = ['k', 'r', 'b', 'g', 'm', 'c']


def metadata(protocol_dict, DEnM_df):
    """
    Plot Lavg, Tavg, and Havg daily.

    metadata(protocol_dict, DEnM_df) -> None

    input protocol_dict: information about the protocol used for this experiment
    input DEnM_df:       pd.dataframe of data from DEnM file
    """

    (dates, start_date, end_date) = analyze.calculate_dates(protocol_dict, DEnM_df)

    # create name for pdf and open multi-page pdf object
    savename = '_'.join(['DEnM', str(protocol_dict['DEnM']) + '.pdf'])
    pdf = PdfPages(savename)

    for day in range(1, len(dates)):
        start = start_date + dt.timedelta(days=(day - 1))
        end = start_date + dt.timedelta(day)

        if end > end_date:
            continue  # exit if on the partial last day

        fig, ax = plt.subplots(3, sharex=True)

        # plot the average light intensity, temperature, and relative humidity
        L = DEnM_df['Lavg'].ix[start:end]
        T = DEnM_df['Tavg'].ix[start:end]
        H = DEnM_df['Havg'].ix[start:end]
        ax[0].plot_date(L.index, L, '-', color='k')
        ax[1].plot_date(L.index, T, '-', color='r')
        ax[2].plot_date(L.index, H, '-', color='b')

        # set title
        ax[0].set_title(' '.join(['DEnM',
                                  str(protocol_dict['DEnM']),
                                  'Day',
                                  str(day)]))

        # set decorations for Lavg graphs (and title)
        ax[0].set_ylabel('light (lux)')
        ax[0].set_ylim(0, 400)
        ax[0].set_xlim(start, end)
        ax[0].xaxis.grid(True, which='major')
        ax[0].yaxis.set_ticks(np.arange(0, 400, 100))

        # set decorations for Tavg graphs
        ax[1].set_ylabel('temp ($^\circ$C)')
        ax[1].set_ylim(18, 36)
        ax[0].set_xlim(start, end)
        ax[1].xaxis.grid(True, which='major')
        ax[1].yaxis.set_ticks(np.arange(18, 36, 5))

        # set decorations for Havg graphs (and shared x axis)
        ax[2].set_ylabel('rel hum (%)')
        ax[2].set_ylim(55, 75)
        ax[0].set_xlim(start, end)
        ax[2].xaxis.grid(True, which='major')
        ax[2].yaxis.set_ticks(np.arange(55, 75, 5))

        # make the x axis shared and pretty
        ax[2].xaxis.set_major_locator(mpld.HourLocator(interval=1))
        ax[2].xaxis.set_major_formatter(mpld.DateFormatter('%H'))
        plt.setp([a.get_xticklabels() for a in fig.axes[:-1]], visible=False)
        fig.subplots_adjust(hspace=0)

        # save plot to pdf and close figure
        pdf.savefig()
        plt.close()
    pdf.close()


def data(protocol_dict, DEnM_df, data_dict, genotype_list, data_type):
    """
    Plot data for arbitrarily many lines on one graph.

    data(protocol_dict, DEnM_df, data_dict, genotype_list, data_type) -> None

    input protocol_dict: information about the protocol used for this experiment
    input DEnM_df:       pd.dataframe of data from DEnM file
    input data_dict:     activity_dict or sleep_dict
    input genotype_list: list of genotypes to plot
    input data_type:     'activity' or 'sleep'
    """

    (dates, start_date, end_date) = analyze.calculate_dates(protocol_dict, DEnM_df)

    # create string used to control binning size
    resample_freq = str(protocol_dict['bin']) + 'Min'

    # create the time series to be used for the dataframes
    t_index = DEnM_df.ix[start_date:end_date].resample(resample_freq, how='sum').index

    # create temporary dataframes to hold the mean and sem
    mean_df = pd.DataFrame(index=t_index)
    sem_df = pd.DataFrame(index=t_index)
    for genotype in genotype_list:
        df = data_dict[genotype][start_date:end_date].resample(resample_freq,
                                                               how='sum')
        mean_df[genotype] = df.mean(axis=1)
        sem_df[genotype] = df.std(axis=1) / math.sqrt(df.shape[1])

    # plot decorations/parameters based on plot type
    plot_decorations = {'activity': ('beam crossings per ' + str(protocol_dict['bin']) + ' minutes', (0, 100)),
                        'sleep':    ('minutes sleep per ' + str(protocol_dict['bin']) + ' minutes', (0, 30))}
    (ylabel, ylim) = plot_decorations[data_type]
    light_bar = ylim[1]

    # other plot parameters
    xlabel = 'time (h)'
    gender_labels = {'f': ur'$\u2640$', 'm': ur'$\u2642$'}
    if protocol_dict['gender'] in gender_labels:
        gender = gender_labels[protocol_dict['gender']]
    else:
        gender = ur''

    # create name for pdf and open multi-page pdf object
    savename = '_'.join([genotype_list[-1], protocol_dict['effector'], protocol_dict['gender'], data_type + '.pdf'])
    pdf = PdfPages(savename)

    for day in range(1, len(dates)):

        start = start_date + dt.timedelta(days=(day - 1))
        end = start_date + dt.timedelta(day)

        if end > end_date: continue  # exit if on the partial last day

        __, ax = plt.subplots()

        # plot each genotype as well as any controls on a graph
        for gen_index, genotype in enumerate(genotype_list):
            if len(genotype_list) > 1:
                color = COLOR_CYCLE[gen_index % len(COLOR_CYCLE)]
            else:
                color = 'r'
            legend_label = ' '.join([genotype, 'N=' + str(data_dict[genotype].shape[1])])
            ax.plot_date(mean_df[start:end].index, mean_df[start:end][genotype], '-', label=legend_label,
                         color=color)
            for i in mean_df[start:end].index:
                ax.errorbar(x=i,
                            y=mean_df[genotype][i], yerr=sem_df[genotype][i],
                            color=color)

        mean_temp = round(DEnM_df['Tavg'].ix[start:end].mean(), 1)
        ax.set_title(' '.join([genotype_list[-1], 'x', protocol_dict['effector'], gender, data_type, 'Day', str(day), '(' + str(mean_temp) + '$^\circ$C' + ')']))
        ax.xaxis.set_major_locator(mpld.HourLocator(interval=1))
        ax.xaxis.set_major_formatter(mpld.DateFormatter('%H'))
        ax.xaxis.grid(True, which='major')
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_ylim(ylim)
        ax.set_xlim(start, end)

        # Shink current axis's height by 10% on the bottom
        box = ax.get_position()
        ax.set_position([box.x0, box.y0 + box.height * 0.1, box.width, box.height * 0.9])

        # Put a legend below current axis
        if len(genotype_list) > 1:
            ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05), prop={'size': 'x-small'})

        # plot dark line for D phase
        if day < protocol_dict['DD']:
            ax.axhline(y=light_bar, xmin=0.5, xmax=1, linewidth=3, color='k')
        else: ax.axhline(y=light_bar, xmin=0, xmax=1, linewidth=3, color='k')

        # save plot to pdf and close figure
        pdf.savefig()
        plt.close()
    pdf.close()


if __name__ == '__main__':
    pass
