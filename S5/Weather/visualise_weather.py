"""
Post simulation analysis tool
Script to plot the car through time and space overlaid on top of the weather contours.
This version have the distance on the x-axis
WIP
"""
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
