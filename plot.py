'''
Created on Mar 6, 2014

@author: William Rowell
'''

from matplotlib.backends.backend_pdf import PdfPages
import math
import analyze
import datetime as dt
import matplotlib.dates as mpld
import matplotlib.pyplot as plt
import numpy as np


def metadata(protocol_dict, DEnM_df):
    '''
    Plot Lavg, Tavg, and Havg daily.
    '''
    (dates, start_date, end_date) = \
        analyze.calculate_dates(protocol_dict, DEnM_df)

    savename = '_'.join(['DEnM', str(protocol_dict['DEnM']) + '.pdf'])

    pdf = PdfPages(savename)

    for day in range(1, len(dates)):
        start = start_date + dt.timedelta(days=(day - 1))
        end = start_date + dt.timedelta(day)

        if end > end_date: continue  # exit if on the partial last day

        fig, ax = plt.subplots(3, sharex=True)

        L = DEnM_df['Lavg'].ix[start:end]
        T = DEnM_df['Tavg'].ix[start:end]
        H = DEnM_df['Havg'].ix[start:end]

        ax[0].plot_date(L.index, L, '-', color='k')
        ax[1].plot_date(L.index, T, '-', color='k')
        ax[2].plot_date(L.index, H, '-', color='k')

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

        pdf.savefig()
        plt.close()

    pdf.close()


def data(protocol_dict, DEnM_df, data_dict, genotype, data_type):
    '''
    Plot given sleep or activity data daily.
    '''

    (dates, start_date, end_date) = \
        analyze.calculate_dates(protocol_dict, DEnM_df)

    resample_freq = str(protocol_dict['bin']) + 'Min'

    data_df = data_dict[genotype].ix[start_date:end_date].resample(resample_freq, how='sum')

    if data_type == 'activity':
        ylabel = 'beam crossings per ' + str(protocol_dict['bin']) + ' minutes'
        ylim = (0, 100)
    if data_type == 'sleep':
        ylabel = 'minutes sleep per ' + str(protocol_dict['bin']) + ' minutes'
        ylim = (0, 45)
    light_bar = 0.95 * ylim[1]

    xlabel = 'time (h)'
    if protocol_dict['gender'] == 'f': gender = ur'$\u2640$'
    elif protocol_dict['gender'] == 'm': gender = ur'$\u2642$'
    else: gender = ur''


    savename = '_'.join([genotype,
                         protocol_dict['gender'],
                         data_type + '.pdf'])

    pdf = PdfPages(savename)

    for day in range(1, len(dates)):

        start = start_date + dt.timedelta(days=(day - 1))
        end = start_date + dt.timedelta(day)

        if end > end_date: continue  # exit if on the partial last day

        __, ax = plt.subplots()

        mean = data_df.mean(axis=1).ix[start:end]
        sem = data_df.std(axis=1).ix[start:end] / math.sqrt(data_df.shape[1])

        ax.plot_date(mean.index, mean, '.-', color='k')
        ax.set_title(' '.join([genotype, gender, data_type, 'Day', str(day),
                               '(N=' + str(data_df.shape[1]) + ')']))

        ax.xaxis.set_major_locator(mpld.HourLocator(interval=1))
        ax.xaxis.set_major_formatter(mpld.DateFormatter('%H'))
        ax.xaxis.grid(True, which='major')
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_ylim(ylim)
        ax.set_xlim(start, end)

        # plot SEM
        for i in mean.index:
            ax.errorbar(x=i, y=mean[i], yerr=sem[i], color='k')

        # plot dark line for D phase
        if day < protocol_dict['DD']:
            ax.axhline(y=light_bar, xmin=0.5, xmax=1, linewidth=5, color='k')
        else: ax.axhline(y=light_bar, xmin=0, xmax=1, linewidth=5, color='k')

        pdf.savefig()
        plt.close()

    pdf.close()

def data_vs_control(protocol_dict, DEnM_df, data_dict, genotype, data_type):
    '''
    Plot given sleep/activity data vs control sleep/activity daily.
    '''

    (dates, start_date, end_date) = \
        analyze.calculate_dates(protocol_dict, DEnM_df)

    resample_freq = str(protocol_dict['bin']) + 'Min'

    control_genotype = protocol_dict['control_genotype']

    data_df = data_dict[genotype].ix[start_date:end_date].resample(resample_freq, how='sum')
    cont_df = data_dict[control_genotype].ix[start_date:end_date].resample(resample_freq, how='sum')

    if data_type == 'activity':
        ylabel = 'beam crossings per ' + str(protocol_dict['bin']) + ' minutes'
        ylim = (0, 100)
    if data_type == 'sleep':
        ylabel = 'minutes sleep per ' + str(protocol_dict['bin']) + ' minutes'
        ylim = (0, 45)
    light_bar = 0.8 * ylim[1]

    xlabel = 'time (h)'
    if protocol_dict['gender'] == 'f': gender = ur'$\u2640$'
    elif protocol_dict['gender'] == 'm': gender = ur'$\u2642$'
    else: gender = ur''


    savename = '_'.join([genotype,
                         'vs',
                         control_genotype,
                         protocol_dict['gender'],
                         data_type + '.pdf'])

    pdf = PdfPages(savename)

    for day in range(1, len(dates)):

        start = start_date + dt.timedelta(days=(day - 1))
        end = start_date + dt.timedelta(day)

        if end > end_date: continue  # exit if on the partial last day

        __, ax = plt.subplots()

        data_mean = data_df.mean(axis=1).ix[start:end]
        data_sem = data_df.std(axis=1).ix[start:end] / math.sqrt(data_df.shape[1])
        cont_mean = cont_df.mean(axis=1).ix[start:end]
        cont_sem = cont_df.std(axis=1).ix[start:end] / math.sqrt(data_df.shape[1])

        ax.plot_date(data_mean.index,
                     data_mean, '-', color='b',
                     label=genotype)
        # plot SEM
        for i in data_mean.index:
            ax.errorbar(x=i, y=data_mean[i], yerr=data_sem[i], color='b')

        ax.plot_date(cont_mean.index,
                     cont_mean,
                     '--', color='r',
                     label=control_genotype)
        # plot SEM
        for i in cont_mean.index:
            ax.errorbar(x=i, y=cont_mean[i], yerr=cont_sem[i], color='r')

        ax.legend(loc=2)

        ax.set_title(' '.join([genotype, gender, data_type, 'Day', str(day),
                               '(N=' + str(data_df.shape[1]) + ')']))
        ax.xaxis.set_major_locator(mpld.HourLocator(interval=1))
        ax.xaxis.set_major_formatter(mpld.DateFormatter('%H'))
        ax.xaxis.grid(True, which='major')
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_ylim(ylim)
        ax.set_xlim(start, end)

        # plot dark line for D phase
        if day < protocol_dict['DD']:
            ax.axhline(y=light_bar, xmin=0.5, xmax=1, linewidth=3, color='k')
        else: ax.axhline(y=light_bar, xmin=0, xmax=1, linewidth=3, color='k')

        pdf.savefig()
        plt.close()

    pdf.close()

def multiple_data(protocol_dict, DEnM_df, data_dict, genotype_list, data_type):
    '''
    Plot data for arbitrarily many lines on one graph.
    '''
    (dates, start_date, end_date) = \
        analyze.calculate_dates(protocol_dict, DEnM_df)

    resample_freq = str(protocol_dict['bin']) + 'Min'

    control_genotype = protocol_dict['control_genotype']

    data_df = data_dict[genotype].ix[start_date:end_date].resample(resample_freq, how='sum')
    cont_df = data_dict[control_genotype].ix[start_date:end_date].resample(resample_freq, how='sum')

    if data_type == 'activity':
        ylabel = 'beam crossings per ' + str(protocol_dict['bin']) + ' minutes'
        ylim = (0, 100)
    if data_type == 'sleep':
        ylabel = 'minutes sleep per ' + str(protocol_dict['bin']) + ' minutes'
        ylim = (0, 45)
    light_bar = 0.8 * ylim[1]

    xlabel = 'time (h)'
    if protocol_dict['gender'] == 'f': gender = ur'$\u2640$'
    elif protocol_dict['gender'] == 'm': gender = ur'$\u2642$'
    else: gender = ur''


    savename = '_'.join([genotype,
                         'vs',
                         control_genotype,
                         protocol_dict['gender'],
                         data_type + '.pdf'])

    pdf = PdfPages(savename)

    for day in range(1, len(dates)):

        start = start_date + dt.timedelta(days=(day - 1))
        end = start_date + dt.timedelta(day)

        if end > end_date: continue  # exit if on the partial last day

        __, ax = plt.subplots()

        data_mean = data_df.mean(axis=1).ix[start:end]
        data_sem = data_df.std(axis=1).ix[start:end] / math.sqrt(data_df.shape[1])
        cont_mean = cont_df.mean(axis=1).ix[start:end]
        cont_sem = cont_df.std(axis=1).ix[start:end] / math.sqrt(data_df.shape[1])

        ax.plot_date(data_mean.index,
                     data_mean, '-', color='b',
                     label=genotype)
        # plot SEM
        for i in data_mean.index:
            ax.errorbar(x=i, y=data_mean[i], yerr=data_sem[i], color='b')

        ax.plot_date(cont_mean.index,
                     cont_mean,
                     '--', color='r',
                     label=control_genotype)
        # plot SEM
        for i in cont_mean.index:
            ax.errorbar(x=i, y=cont_mean[i], yerr=cont_sem[i], color='r')

        ax.legend(loc=2)

        ax.set_title(' '.join([genotype, gender, data_type, 'Day', str(day),
                               '(N=' + str(data_df.shape[1]) + ')']))
        ax.xaxis.set_major_locator(mpld.HourLocator(interval=1))
        ax.xaxis.set_major_formatter(mpld.DateFormatter('%H'))
        ax.xaxis.grid(True, which='major')
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_ylim(ylim)
        ax.set_xlim(start, end)

        # plot dark line for D phase
        if day < protocol_dict['DD']:
            ax.axhline(y=light_bar, xmin=0.5, xmax=1, linewidth=3, color='k')
        else: ax.axhline(y=light_bar, xmin=0, xmax=1, linewidth=3, color='k')

        pdf.savefig()
        plt.close()

    pdf.close()



if __name__ == '__main__':
    pass
