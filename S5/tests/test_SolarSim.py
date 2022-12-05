import os
import pytest
from unittest import mock
import multiprocessing as mp
import subprocess as sp

import S5.HPC.file_io as S5io
import S5.HPC.SolarSim as SS
import numpy as np
from S5 import Tecplot as TP
import pandas as pd
from pandas.testing import assert_frame_equal
from itertools import cycle
import sys


@pytest.fixture(scope='function')
def mock_Popen(mock_sp):
    with mock.patch.object(sp, "Popen") as mock_Popen:
        mock_Popen.return_value = mock_sp
        yield mock_Popen


@pytest.fixture(scope='function')
def mock_sp():
    mock_sp = mock.MagicMock(name='mock_sp')
    mock_stdout = mock.MagicMock(name='mock_sp.stdout')
    mock_sp.poll = mock.MagicMock(side_effect=cycle([1, 1, None]))
    mock_sp.stdout = mock_stdout
    return mock_sp


@pytest.fixture()
def mock_read_history(history_file):
    mock_result = S5io.read_history(history_file)
    with mock.patch.object(SS, 'read_history', autospec=True) as mock_read_history:
        mock_read_history.return_value = mock_result
        yield mock_read_history


@pytest.mark.parametrize('SS_mode', ['HPC', "Normal"])
def test_run_ss(mock_Popen, SS_mode):
    solarsim_location = r'.\SolarSim4.1.exe'
    control = r'SolarSim.in'
    summary = r'Summary.dat'
    history = r'History.dat'
    solartotals = r'SolarTotals.dat'
    if SS_mode == 'HPC':
        mock_Popen.return_value.readline = mock.MagicMock(return_value=b'Read in OK.\n')
    elif SS_mode == 'Normal':
        mock_Popen.return_value.readline = mock.MagicMock(
            return_value=b'DDHHMM=010830  DrivingTime=     1s  Distance=   0 km  LapN=  1   DistanceWithinLap=  0.0 km   CarVel=  0.0 km/h   YawAngle=86.8 deg ControllerPower=-3000.0 W  Battery= 98.0 %  AverageVel=  0.0 km/h  SolarPower=353.1 W\n')
    SS.run_ss(solarsim_location, control, summary, history, solartotals)
    mock_Popen.assert_called_once_with([solarsim_location, control, summary, history, solartotals], stdout=sp.PIPE)


def test_run_ss_with_lock(mock_Popen):
    solarsim_location = r'.\SolarSim4.1.exe'
    control = r'SolarSim.in'
    summary = r'Summary.dat'
    history = r'History.dat'
    solartotals = r'SolarTotals.dat'
    lock = mp.Lock()
    lock.acquire()
    SS.run_ss(solarsim_location, control, summary, history, solartotals, lock)
    mock_Popen.assert_called_once_with([solarsim_location, control, summary, history, solartotals], stdout=sp.PIPE)


def test_run_ss_timeout(mock_Popen, monkeypatch, capsys):
    mock_Popen.return_value.poll = mock.MagicMock(return_value=None)
    solarsim_location = r'.\SolarSim4.1.exe'
    control = r'SolarSim.in'
    summary = r'Summary.dat'
    history = r'History.dat'
    solartotals = r'SolarTotals.dat'
    lock = mp.Lock()
    lock.acquire()
    monkeypatch.setattr(np, "timedelta64", mock.MagicMock(return_value=0))
    SS.run_ss(solarsim_location, control, summary, history, solartotals, lock)
    mock_Popen.assert_called_once_with([solarsim_location, control, summary, history, solartotals], stdout=sp.PIPE)
    assert capsys.readouterr().out.find("SolarSim process timeout. Potential deadlock from subprocess.Popen, consider " \
                                        "increasing SolarSim update interval")


def test_const_vel(tmp_path, mock_Popen):
    solarsim_location = r'.\SolarSim4.1.exe'
    control = r'SolarSim.in'
    summary = r'Summary.dat'
    history = r'History.dat'
    solartotals = r'SolarTotals.dat'
    lock = mp.Lock()
    t_vel = 70.2
    original_dir = os.getcwd()
    os.chdir(tmp_path)
    SS.const_vel(lock, t_vel, solarsim_location, control, summary, history, solartotals)

    os.chdir(original_dir)
    vel = TP.TecplotData(tmp_path / "TargetVel.dat")
    correct_df = pd.DataFrame([[0, t_vel], [3030, t_vel]], columns=['Distance (km)', 'TargetVel (km/h)'])
    assert_frame_equal(vel.data, correct_df, check_dtype=False)
    assert vel.zone.ni == 2


def test_vel_sweep_output_filename(tmp_path, mock_Popen, monkeypatch):
    vel_list = [70.2]
    solarsim_location = r'.\SolarSim4.1.exe'
    original_dir = os.getcwd()
    os.chdir(tmp_path)
    mock_Popen.return_value.readline = mock.MagicMock(return_value=b'Read in OK.\n')

    SS.vel_sweep(vel_list, solarsim_location)
    os.chdir(original_dir)
    v = vel_list[0]
    mock_Popen.assert_called_once_with([solarsim_location, "SolarSim.in", f"Summary_{v}.dat", f"History_{v}.dat",
                                        f"SolarTotals_{v}.dat"], stdout=sp.PIPE)


def test_vel_sweep_times_called(tmp_path, mock_Popen, monkeypatch):
    vel_list = [i for i in range(60, 70)]
    solarsim_location = r'.\SolarSim4.1.exe'
    original_dir = os.getcwd()
    os.chdir(tmp_path)
    mock_Popen.return_value.readline = mock.MagicMock(return_value=b'Read in OK.\n')

    SS.vel_sweep(vel_list, solarsim_location)
    os.chdir(original_dir)
    assert mock_Popen.call_count == len(vel_list)


@pytest.mark.skip('Tests for multiprocessing functions to be implemented')
def test_vel_sweep_par():
    # TODO: fix tests involveing multiprocessing
    pass


# TODO:improve to test the content of the output dataframe
def test_read_vel_sweep(tmp_path, mock_read_history):
    vel_list = [i for i in range(65, 70)]

    output = SS.read_vel_sweep(vel_list, path=tmp_path)
    assert mock_read_history.call_count == len(vel_list)
    v = vel_list[-1]
    mock_read_history.assert_called_with(os.path.join(tmp_path, f"History_{v}.dat"))
    assert isinstance(output, pd.DataFrame)


def test_file_swap(tmp_path):
    solarsim_location = r'.\SolarSim4.1.exe'
    control = r'SolarSim.in'
    summary = r'Summary.dat'
    history = r'History.dat'
    solartotals = r'SolarTotals.dat'
    lock = mp.Lock()
    runname = r'Tvel.dat'
    filename = r'TargetVel.dat'
    original_dir = os.getcwd()
    os.chdir(tmp_path)

    #  create fake files to check renaming works
    S5io.write_vel(69, r'TargetVel.dat')
    with mock.patch.object(SS, 'run_ss', autospec=True) as mock_run_ss:
        SS.file_swap(lock, filename, runname, solarsim_location, control, summary, history, solartotals)
    mock_run_ss.assert_called_once_with(solarsim_location, control, summary, history, solartotals, lock)
    assert runname in os.listdir()
    assert filename in os.listdir()
    with open(filename) as original:
        with open(runname) as replaced:
            assert original.readlines() == replaced.readlines()
    os.chdir(original_dir)


def test_file_sweep_output_filename(mock_Popen, tmp_path):
    file_list = ['MPPT13.1.dat']
    runname = 'Array.dat'
    solarsim_location = r'.\SolarSim4.1.exe'
    original_dir = os.getcwd()
    os.chdir(tmp_path)
    mock_Popen.return_value.readline = mock.MagicMock(return_value=b'Read in OK.\n')
    with open(file_list[0], 'w') as fopen:
        fopen.write('this is a test dummy file.')

    SS.file_sweep(file_list, runname, solarsim_location)
    os.chdir(original_dir)

    file = file_list[0]
    mock_Popen.assert_called_once_with([solarsim_location, "SolarSim.in", f"Summary_{file}",
                                        f"History_{file}", f"SolarTotals_{file}"], stdout=sp.PIPE)


def test_file_sweep_times_called(tmp_path, mock_Popen, monkeypatch):
    file_list = [f'MPPT13.{i}.dat' for i in range(5)]
    runname = 'Array.dat'
    solarsim_location = r'.\SolarSim4.1.exe'
    original_dir = os.getcwd()
    os.chdir(tmp_path)
    monkeypatch.setattr(SS, 'copyfile', mock.MagicMock())
    mock_Popen.return_value.readline = mock.MagicMock(return_value=b'Read in OK.\n')

    SS.file_sweep(file_list, runname, solarsim_location)
    os.chdir(original_dir)
    assert mock_Popen.call_count == len(file_list)


@pytest.mark.skip('Tests for multiprocessing functions to be implemented')
def file_sweep_par():
    # TODO: fix tests involveing multiprocessing
    pass


# TODO:improve to test the content of the output dataframe
def test_read_file_sweep(tmp_path, mock_read_history):
    file_list = [f'MPPT13.{i}.dat' for i in range(5)]
    output = SS.read_file_sweep(file_list, path=tmp_path)
    assert mock_read_history.call_count == len(file_list)
    f = file_list[-1]
    mock_read_history.assert_called_with(os.path.join(tmp_path, f"History_{f}"))
    assert isinstance(output, pd.DataFrame)
