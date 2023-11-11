"""
Functions to visualise Strategy related data.
"""
import os
from typing import Union, Tuple

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import dates

import S5.Tecplot as TP

matplotlib.rcParams.update(
    {
        "pgf.texsystem": "pdflatex",
        "font.family": "serif",
        "text.usetex": False,
        "pgf.rcfonts": False,
        "font.size": 8,
    }
)

plt.rcParams.update({"font.serif": "Times New Roman"})


def plot_contor(
        contour_parameter: str,
        weather: TP.SSWeather,
        display_name: str = "",
        cmap="viridis",
        ax=None,
        **kwargs,
) -> Tuple[plt.Figure, plt.Axes]:
    """Plots a variable from the weather file as a contour map.

    The plot will have space in the x-axis and time in the y-axis.

    Args:
        contour_parameter: Column name of the parameter to plot.
        weather: Weather file containing the data.
        display_name: Name of the variable to label the figure.
        cmap: Colormap to use, passed onto matplotlib.axes.Axes.pcolormesh,
            default to be 'viridis'.
        ax: Optional, if present then this will be axes to plot on.
        **kwargs: Additional arguments to pass along to
            matplotlib.axes.Axes.pcolormesh.

    Returns:
        A tuple of (figure, axes)

    Examples:
        >>> weather = TP.SSWeather("C:/path/to/Weather.dat")
        >>> weather.add_timestamp('20231023')
        >>> plot_contor(
        >>>     "DirectSun (W/m2)",
        >>>     weather,
        >>>     display_name="Direct Irradiation (W/m²)",
        >>>     cmap="inferno",
        >>>     ax=ax[0],
        >>> )
    """
    cont = weather.data.loc[:, [contour_parameter]].to_numpy()
    dist = np.unique(weather.data.loc[:, ["Distance (km)"]].to_numpy())
    date_time = np.unique(weather.data.loc[:, ["DateTime"]].to_numpy())

    date_timenum, dist = np.meshgrid(dates.date2num(date_time), dist)
    plotvel = np.reshape(cont, np.shape(dist))
    if ax is None:
        fig, ax = plt.subplots()
    else:
        fig = ax.get_figure()

    # plot the contour
    c = ax.pcolormesh(dist, date_timenum, plotvel, cmap=cmap, **kwargs)
    cbar = fig.colorbar(c, ax=ax)
    cbar.set_label(display_name, rotation=270, labelpad=10)
    yticks = dates.num2date(ax.get_yticks())
    yticks = [out.strftime("%d-%m-%Y\n%H:%M ") for out in yticks]
    ax.set_yticklabels(yticks)

    # Format the figure
    ax.set_title(display_name)
    ax.set_xlim([0, 3030])
    ax.set_xlabel("Distance (km)")
    ax.set_ylabel("Time")
    return fig, ax


def plot_trace(
        hist: TP.SSHistory, ax: plt.Axes = None, set_limit=True, **kwargs
) -> Tuple[plt.Figure, plt.Axes]:
    """Plots the location of the car on a time-distance graph.

    This can be used in conjunction with plot_contor to show how the car is
    positioned in relation to clouds or period of high wind.
    Requires the columns 'DateTime' and 'Distance(km)' present in the DataFrame.

    Args:
        hist: History file to plot the trace.
        ax: Optional, axes to plot the trace on.
        set_limit: Set the axes limit only to the period where position data is
            present
        **kwargs: Additional arguments to pass along to matplotlib.pyplot.plot.

    Returns:
        A tuple of (figure, axes)

    Raises:
        KeyError: If DateTime is not present in

    Examples:
        >>> history = TP.SSHistory("C:/path/to/History.dat")
        >>> weather = get_weather(history.filename)
        >>> history.add_timestamp('20231023')
        >>> weather.add_timestamp('20231023')
        >>> plot_contor(
        >>>     "DirectSun (W/m2)",
        >>>     weather,
        >>>     display_name="Direct Irradiation (W/m²)",
        >>>     cmap="inferno",
        >>>     ax=ax[0],
        >>> )
        >>> plot_trace(hist=history, ax=ax[0], lw=2)
    """
    if "DateTime" not in hist.data.columns:
        raise KeyError(
            "DateTime column not present in History file, consider "
            "using history.add_timestamp to add the datetime colum."
        )
    if ax is None:
        fig, ax = plt.subplots()
    else:
        fig = ax.get_figure()
    ax.plot(hist.data["Distance(km)"], hist.data["DateTime"], **kwargs)
    if set_limit:
        ax.set_ylim(
            dates.date2num(hist.data["DateTime"].min()) - 1 / 24,
            dates.date2num(hist.data["DateTime"].max()) + 1 / 24,
        )
    return fig, ax


def plot_airspeed(
        history: TP.SSWeather, **kwargs
) -> plt.Figure:
    """

    Args:
        history: History file, with DataTime as index
        **kwargs: Additional arguments to pass along to matplotlib.pyplot.plot.

    Returns:
        Figure containing all the plots
    """
    if "marker" not in kwargs:
        kwargs["marker"] = "."

    hist = history.data
    hist = hist.set_index("DateTime")
    hist["Day"] = hist["DDHHMMSS"] // 1000000
    hist = hist[hist["CarVel(m/s)"] != 0]
    hist["AirSpeed(m/s)"] = hist["CarVel(m/s)"] + hist["HeadWind(m/s)"]

    fig, ax = plt.subplots(nrows=hist["Day"].nunique(), ncols=2)
    fig.set_size_inches(8.3, 11.7)
    fig.suptitle(history.filename)
    fig.tight_layout(rect=(0.11, 0.02, 1, 0.98))

    for i, day in enumerate(hist["Day"].unique()):
        hist[hist["Day"] == day][["AirSpeed(m/s)"]].plot(
            subplots=True, ax=ax[i, 0], **kwargs
        )
        hist[hist["Day"] == day][["HeadWind(m/s)"]].plot(
            subplots=True, ax=ax[i, 1], **kwargs
        )
        ax[i, 0].set_ylim([19, 30])  # TODO: better way to set limits.
        ax[i, 0].set_title(f"{os.path.basename(history.filename)} Day {day}")
    return fig


def get_weather(history_path: Union[str, os.PathLike]) -> TP.SSWeather:
    """Get the corresponding weather file for the given history file.

    The Weather file is found by looking at SolarSim.in at the same folder as
    the history file.

    Args:
        history_path: Path to the history file.

    Returns:
        Weather file object.

    Examples:
        >>> history = TP.SSHistory("C:/path/to/History.dat")
        >>> weather = get_weather(history.filename)
    """
    control = TP.DSWinput(
        os.path.join(os.path.dirname(history_path), "SolarSim.in")
    )
    weather = TP.SSWeather(
        os.path.join(
            os.path.dirname(history_path),
            control.get_value("WeatherFile").strip('"'),
        )
    )
    return weather
