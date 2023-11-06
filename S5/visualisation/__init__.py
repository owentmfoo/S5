"""
Post simulation analysis scripts
Script to plot the car through time and space overlaid on top of the weather contours.
This version have the distance on the x-axis
WIP
"""
import os

import matplotlib
import matplotlib.dates as dates
import matplotlib.pyplot as plt
import numpy as np

import S5.Tecplot as TP

matplotlib.rcParams.update({
    "pgf.texsystem": "pdflatex",
    'font.family': 'serif',
    'text.usetex': False,
    'pgf.rcfonts': False,
    'font.size': 8,
})

plt.rcParams.update({'font.serif': 'Times New Roman'})


def plot_contors(contour_parameter, weather, VarName='', cmap='viridis',
                 ax=None,
                 **kwargs):
    cont = weather.data.loc[:, [contour_parameter]].to_numpy()
    Dist = np.unique(weather.data.loc[:, ['Distance (km)']].to_numpy())
    DateTime = np.unique(weather.data.loc[:, ['DateTime']].to_numpy())

    DateTimenum, Dist = np.meshgrid(dates.date2num(DateTime), Dist)
    plotvel = np.reshape(cont, np.shape(Dist))
    if ax is None:
        fig, ax = plt.subplots()
    else:
        fig = ax.get_figure()

    # plot the contour
    c = ax.pcolormesh(Dist, DateTimenum, plotvel, cmap=cmap, **kwargs)
    cbar = fig.colorbar(c, ax=ax)
    cbar.set_label(VarName, rotation=270, labelpad=10)
    yticks = dates.num2date(ax.get_yticks())
    yticks = [out.strftime("%d-%m-%Y\n%H:%M ") for out in yticks]
    ax.set_yticklabels(yticks)

    # Format the figure
    ax.set_title(VarName)
    ax.set_xlim([0, 3030])
    ax.set_xlabel("Distance (km)")
    ax.set_ylabel("Time")
    return fig, ax


def save_fig(fig: plt.figure, outname: str):
    fig.set_size_inches(6, 8)
    fig.subplots_adjust(top=0.9, bottom=0.12, left=0.1, right=1.05, hspace=0,
                        wspace=0)
    fig.set_dpi(150)
    fig.show()

    outname = outname.rstrip(".pdf").rstrip(".png")
    fig.savefig(f'{outname}.png')


def plot_trace(hist, ax=None, **kwargs):
    ax.plot(hist.data['Distance(km)'], hist.data['DateTime'], **kwargs)
    ax.set_ylim([dates.date2num(hist.data['DateTime'].min()) - 1 / 24,
                 dates.date2num(hist.data['DateTime'].max()) + 1 / 24])


def plot_airspeed(history_path):
    HISTORY = TP.SSHistory(history_path)
    HISTORY.add_timestamp(startday=START_DATE)
    hist = HISTORY.data
    hist = hist.set_index('DateTime')
    hist['Day'] = hist['DDHHMMSS'] // 1000000
    hist['km500'] = hist['Distance(km)'] // 500
    filter = hist['CarVel(m/s)'] == 0
    hist = hist[filter == False]
    # Get the average wind speed per day
    hist['AirSpeed(m/s)'] = hist['CarVel(m/s)'] + hist['HeadWind(m/s)']
    fig, ax = plt.subplots(nrows=hist['Day'].nunique(), ncols=2)
    fig.set_size_inches(8.3, 11.7)
    # fig.set_dpi(150)
    fig.suptitle(HISTORY.filename)
    fig.tight_layout(rect=(0.11, 0.02, 1, 0.98))
    for i, day in enumerate(hist['Day'].unique()):
        hist[hist['Day'] == day][['AirSpeed(m/s)']].plot(subplots=True,
                                                         marker='.', ax=ax[
                i, 0])  # TODO: allow this to be override by some way?
        hist[hist['Day'] == day][['HeadWind(m/s)']].plot(subplots=True,
                                                         marker='.',
                                                         ax=ax[i, 1])
        ax[i, 0].set_ylim([19, 30])  # TODO: better way to set limits.
        ax[i, 0].set_title(f'{os.path.basename(HISTORY.filename)} Day {day}')
    plt.show()
    return fig


def get_weather(history_path):
    HISTORY = TP.SSHistory(history_path)
    HISTORY.add_timestamp(startday=START_DATE)
    Control = TP.DSWinput(
        os.path.join(os.path.dirname(HISTORY.filename), "SolarSim.in")
    )
    Weather = TP.SSWeather(
        os.path.join(os.path.dirname(HISTORY.filename),
                     Control.get_value("WeatherFile").strip('"'))
    )
    Weather.add_timestamp(startday=START_DATE)
    return Weather


if __name__ == '__main__':
    START_DATE = '20230928'
    Weather = TP.SSWeather(
        r'E:\WSC23\MidRace_VelSweep_Day0\Weather-latest-2023-09-28-Day2.dat')
    Weather.add_timestamp(startday=START_DATE)

    HISTORY = TP.SSHistory(r'E:\WSC23\MidRace_VelSweep_Day0\History_63.dat')
    HISTORY.add_timestamp(startday=START_DATE)
    cm = plt.get_cmap('Set1')

    fig, ax = plt.subplots(nrows=2, sharex=True)
    fig.set_size_inches(6, 8)
    plot_contors('DirectSun (W/m2)', Weather,
                 VarName='Direct Irradiation (W/m²)', cmap='inferno', ax=ax[0]
                 )  # outname="directContor_Dist")
    plot_trace(hist=HISTORY, ax=ax[0], c=cm.colors[0], lw=2)
    plot_contors('DiffuseSun (W/m2)', Weather,
                 VarName='Diffuse Irradiation (W/m²)',
                 cmap='inferno',
                 ax=ax[1]
                 )  # outname="diffuseContor_Dist")
    plot_trace(hist=HISTORY, ax=ax[1], c=cm.colors[0], lw=2)
    fig, ax = plot_contors('WindVel (m/s)', Weather,
                           VarName='Wind Velocity (m/s)',
                           cmap='viridis',
                           )  # outname="windContor_Dist")
    plot_trace(hist=HISTORY, ax=ax, c=cm.colors[0], lw=2)
    fig, ax = plot_contors('WindDir (deg)', Weather, VarName='Wind Dir (deg)',
                           cmap='twilight',
                           )  # outname="windDirContor_Dist")
    plot_trace(hist=HISTORY, ax=ax, c=cm.colors[0], lw=2)
    fig, ax = plot_contors('AirTemp (degC)', Weather,
                           VarName='Air Temperature (°C)',
                           cmap='coolwarm',
                           )  # outname="tempContor_Dist")
    plot_trace(hist=HISTORY, ax=ax, c=cm.colors[0], lw=2)
    fig, ax = plot_contors('AirPress (Pa)', Weather,
                           VarName='Air Pressure (Pa)',
                           cmap='coolwarm',
                           )  # outname="pressContor_Dist")
    plot_trace(hist=HISTORY, ax=ax, c=cm.colors[0], lw=2)
    plt.show()
