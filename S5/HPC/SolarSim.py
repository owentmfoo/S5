import multiprocessing as mp
import os.path
import subprocess as sp
from os import PathLike
from shutil import copyfile
from typing import Union, Optional, List

import numpy as np
import pandas as pd

from S5.HPC.file_io import write_vel, read_history


def run_ss(
        executable_location: Union[str, PathLike],
        control: Union[str, PathLike],
        summary: Union[str, PathLike],
        history: Union[str, PathLike],
        solartotals: Union[str, PathLike],
        lock: Optional[mp.Lock] = None,
) -> None:
    """run solar sim
    :param executable_location: path to SolarSim to execute
    :param control: path to control file
    :param summary: path to write summary file
    :param history: path to write history file
    :param solartotals: path to write solartotals file
    :param lock: multiprocessing lock for parallel computing
    """
    t = np.datetime64("now")
    print(f"SolarSim started at {str(t)}")
    p = sp.Popen(
        [executable_location, control, summary, history, solartotals],
        stdout=sp.PIPE
    )  # run solarsim
    line = p.stdout.readline()
    released = False
    while (p.poll() is None) and (
            (np.datetime64("now") - t) < np.timedelta64(1, "h")):
        # block new solarsim until current solarsim have finish readin
        if line.decode("UTF-8").startswith("DDHHMM") or line.decode(
                "UTF-8").startswith(
                "Read"
        ):
            if lock is not None:
                lock.release()
            released = True
            p.stdout.close()
            break
        line = p.stdout.readline()
    print(f'SolarSim read in completed at {str(np.datetime64("now"))}')

    while p.poll() is None:  # wait for the simulation to complete
        if (np.datetime64("now") - t) > np.timedelta64(1,
                                                       "h"):  # 1 hour timeout
            print(
                "SolarSim process timeout. Potential deadlock from subprocess.Popen, consider increasing SolarSim "
                "update interval"
            )
            p.kill()
            break

    if not released and lock is not None:
        lock.release()
    print(f'SolarSim finished at {str(np.datetime64("now") - t)} started at {t}')


def const_vel(
        lock: mp.Lock,
        t_vel: float,
        executable_location: Union[str, PathLike],
        control: Union[str, PathLike],
        summary: Union[str, PathLike],
        history: Union[str, PathLike],
        solartotals: Union[str, PathLike],
) -> None:
    """run solar sim at const vel t_vel
    :param lock: multiprocessing.lock for parallel computing
    :param t_vel: target velocity to run at
    :param executable_location: path to SolarSim to execute
    :param control: path to control file
    :param summary: path to write summary file
    :param history: path to write history file
    :param solartotals: path to write solartotals file
    """
    lock.acquire()  # block until SS readin complete (released in run_ss)
    write_vel(t_vel)
    print("tvel written")
    run_ss(executable_location, control, summary, history, solartotals, lock)


def vel_sweep(
        vel_list: List[float],
        executable_location: Union[str, PathLike] = "../SolarSim.X"
) -> None:
    """perform a constant velocity sweep with velocities in the list vel_list, parallel version available as
    vel_sweep_par
    :param vel_list: list of floats containing the velocities to run at
    :param executable_location: location of the solarsim executable
    """
    lock = mp.Manager().Lock()
    for v in vel_list:
        const_vel(
            lock,
            v,
            executable_location,
            "SolarSim.in",
            f"Summary_{v}.dat",
            f"History_{v}.dat",
            f"SolarTotals_{v}.dat",
        )


def vel_sweep_par(
        vel_list: List[Union[str, PathLike]],
        executable_location: Union[str, PathLike] = "../SolarSim.X",
        n_jobs: int = mp.cpu_count() - (2 * (mp.cpu_count() <= 16)),
) -> None:
    """perform a constant velocity sweep with velocities in the list vel_list in parallel, parallel version of vel_sweep

    Args:
        vel_list: List of floats containing the velocities to run at.
        executable_location: Location of the solarsim executable
        n_jobs: Number of SolarSims to run in parallel, if less than 16 cpu
            (non-HPC) it will default to number of cpu - 2, else it will be
            the number of cpu available.

    Returns:
        None
    """
    lock = mp.Manager().Lock()
    args = []
    for v in vel_list:
        args.append((
            lock,
            v,
            executable_location,
            "SolarSim.in",
            f"Summary_{v}.dat",
            f"History_{v}.dat",
            f"SolarTotals_{v}.dat",
        ))

    with mp.Pool(min(n_jobs, len(vel_list))) as pool:
        pool.starmap(const_vel, args)
    print("SS complete.")


def read_vel_sweep(
        vel_list: List[float], path: Union[str, PathLike] = "./"
) -> pd.DataFrame:
    """read the set of results of vel_sweep, return dataframe containing key results.
    :param vel_list: list of floats containing the velocities to run at
    :param path: location of the files
    """
    result = pd.DataFrame(
        index=range(len(vel_list)),
        columns=[
            "tVel",
            "drivingTime",
            "DistCovered",
            "SoC",
            "AverageVel",
            "Vstd",
            "SoCMax",
            "SoCMin",
        ],
    )
    for i, v in enumerate(vel_list):
        driving_time, dist, soc, avg_vel, Vstd, SoCMax, SoCMin = read_history(
            os.path.join(path, f"History_{v}.dat")
        )
        result.loc[i, :] = [v, driving_time, dist, soc, avg_vel, Vstd, SoCMax,
                            SoCMin]
        print(f"{v}\t{driving_time}\t {dist}\t{soc}\t{avg_vel}\t{Vstd}")
    return result


def file_swap(
        lock: mp.Lock,
        filename: Union[str, PathLike],
        run_name: Union[str, PathLike],
        executable_location: Union[str, PathLike],
        control: Union[str, PathLike],
        summary: Union[str, PathLike],
        history: Union[str, PathLike],
        solartotals: Union[str, PathLike],
) -> None:
    """swap file in and run SS with it
    :param lock: multiprocessing.lock for parallel computing
    :param filename: filename to be swapped in for solarsim
    :param run_name: name referenced in control file
    :param executable_location: path to SolarSim to execute
    :param control: path to control file
    :param summary: path to write summary file
    :param history: path to write history file
    :param solartotals: path to write solartotals file
    """
    lock.acquire()  # block until SS readin complete (released in run_ss)
    copyfile(filename, run_name)
    print("file swapped")
    run_ss(executable_location, control, summary, history, solartotals, lock)


def file_sweep_par(
        file_list: List[Union[str, PathLike]],
        run_name: Union[str, PathLike],
        executable_location: Union[str, PathLike] = "../SolarSim.X",
        n_jobs: int = mp.cpu_count() - (2 * (mp.cpu_count() <= 16)),
) -> None:
    """sweep files by renaming each of the file in list to run_name and run ss. Block until last SS has read in.

    Args:
        file_list: filename to be swapped in for solarsim
        run_name: name referenced in control file
        executable_location: path to SolarSim to execute
        n_jobs: Number of SolarSims to run in parallel, if less than 16 cpu
            (non-HPC) it will default to number of cpu - 2, else it will be
            the number of cpu available.

    Returns:
        None
    """
    lock = mp.Manager().Lock()
    args = []
    for f in file_list:
        args.append((
            lock,
            f,
            run_name,
            executable_location,
            "SolarSim.in",
            f"Summary_{f}",
            f"History_{f}",
            f"SolarTotals_{f}",
        ))
    with mp.Pool(min(n_jobs, len(file_list))) as pool:
        pool.starmap(file_swap, args)
    print("SS complete.")


def file_sweep(
        file_list: List[Union[str, PathLike]],
        run_name: Union[str, PathLike],
        executable_location: Union[str, PathLike] = "../SolarSim.X",
) -> None:
    """sweep files by renaming each of the file in list to run_name and run ss. Parallel version available as
    file_sweep_par.
    :param file_list: filename to be swapped in for solarsim
    :param run_name: name referenced in control file
    :param executable_location: path to SolarSim to execute
    """
    lock = mp.Manager().Lock()
    for f in file_list:
        file_swap(
            lock,
            f,
            run_name,
            executable_location,
            "SolarSim.in",
            f"Summary_{f}",
            f"History_{f}",
            f"SolarTotals_{f}",
        )


def read_file_sweep(
        file_list: List[Union[str, PathLike]], path: Union[str, PathLike]
) -> pd.DataFrame:
    """read the set of results of file_sweep, return dataframe containing key results.
    :param file_list: list of filename that was swapped in (e.g. tvel_60.dat for History_tvel_60.dat)
    :param path: location of the files
    """
    #  set up output dataframe
    result = pd.DataFrame(
        index=range(len(file_list)),
        columns=[
            "file",
            "drivingTime",
            "DistCovered",
            "SoC",
            "AverageVel",
            "SoCMax",
            "SoCMin",
        ],
    )

    #  fetch the results for each file and put it into the dataframe
    for i, f in enumerate(file_list):
        driving_time, dist, soc, avg_vel, Vstd, SoCMax, SoCMin = read_history(
            os.path.join(path, f"History_{f}")
        )
        result.loc[i, :] = [f, driving_time, dist, soc, avg_vel, SoCMax, SoCMin]
    print(result)
    return result


if __name__ == "__main__":  # pragma: no cover
    import matplotlib.pyplot as plt

    filename = "TargetVel.dat"
    print(mp.cpu_count())

    vel = [v for v in range(50, 51)]
    print(vel)
    vel_sweep(vel, r"..\SolarSim4.1.exe")
    duration = read_vel_sweep(vel,
                              r"W:\DataStorage\OwenFoo\portal_from_hamilton")
    pd.DataFrame(duration).plot()
    plt.plot(duration[1], duration[0], "o")
