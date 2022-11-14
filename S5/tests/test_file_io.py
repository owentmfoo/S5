import random

import pandas as pd
import pytest
from S5.HPC.file_io import *
import S5.Tecplot as TP
from pandas.testing import assert_frame_equal
import pandas as pd
import os

def test_write_vel_int(tmp_path):
    write_vel(70,tmp_path/"TargetVel.dat")
    vel = TP.TecplotData(tmp_path/"TargetVel.dat")
    correct_df = pd.DataFrame([[0,70],[3030,70]],columns=['Distance (km)', 'TargetVel (km/h)'])
    assert_frame_equal(vel.data,correct_df,check_dtype=False)
    assert vel.zone.ni == 2

def test_write_vel_float(tmp_path):
    write_vel(70.0,tmp_path/"TargetVel.dat")
    vel = TP.TecplotData(tmp_path/"TargetVel.dat")
    correct_df = pd.DataFrame([[0,70],[3030,70]],columns=['Distance (km)', 'TargetVel (km/h)'])
    assert_frame_equal(vel.data,correct_df,check_dtype=False)
    assert vel.zone.ni == 2

def test_write_vel_pandas(tmp_path):
    correct_df = pd.DataFrame([[0, 70], [3030, 70]], columns=['Distance (km)', 'TargetVel (km/h)'])
    write_vel(correct_df, tmp_path / "TargetVel.dat")
    vel = TP.TecplotData(tmp_path / "TargetVel.dat")
    assert_frame_equal(vel.data, correct_df, check_dtype=False)
    assert vel.zone.ni == 2

def test_write_vel_default_name(tmp_path,request):
    os.chdir(tmp_path)
    write_vel(70)
    os.chdir(request.config.invocation_dir)
    vel = TP.TecplotData(tmp_path / "TargetVel.dat")
    correct_df = pd.DataFrame([[0, 70], [3030, 70]], columns=['Distance (km)', 'TargetVel (km/h)'])
    assert_frame_equal(vel.data, correct_df, check_dtype=False)
    assert vel.zone.ni == 2

# TODO: improve
def test_history_summary(history_file):
    driving_time, dist, soc, avg_vel, Vstd, SoCMax, SoCMin = read_history(history_file)
    hist = TP.SSHistory(history_file)
    assert hist.data['DrivingTime(s)'].iloc[-1] == driving_time
    assert hist.data['Distance(km)'].iloc[-1] == dist
    assert hist.data['BatteryCharge(%)'].iloc[-1] == soc
    assert  hist.data['AverageCarVel(km/h)'].iloc[-1] == avg_vel
    assert np.std(hist.data[hist.data["Driving"]==1].loc[:,'CarVel(km/h)']) == Vstd
    assert hist.data['BatteryCharge(%)'].max() == SoCMax
    assert hist.data['BatteryCharge(%)'].min() == SoCMin

#TODO:improve
def test_history_summary_avgvel(history_file,tmp_path):
    hist = TP.SSHistory(history_file)
    hist.data.drop(columns=['AverageCarVel(km/h)'],inplace=True)
    dfsize = hist.data.shape[0]
    hist.write_tecplot(tmp_path/'hist_mock.dat')
    driving_time, dist, soc, avg_vel, Vstd, SoCMax, SoCMin = read_history(tmp_path/'hist_mock.dat')
    assert hist.data['DrivingTime(s)'].iloc[-1] == driving_time
    assert hist.data['Distance(km)'].iloc[-1] == dist
    assert hist.data['BatteryCharge(%)'].iloc[-1] == soc
    assert np.std(hist.data[hist.data["Driving"]==1].loc[:,'CarVel(km/h)']) == Vstd
    assert hist.data['BatteryCharge(%)'].max() == SoCMax
    assert hist.data['BatteryCharge(%)'].min() == SoCMin


def test_adjust_v(velocity_file):
    vel = TP.TecplotData(velocity_file)
    adjust_v(vel, 50)
    assert vel.data['TargetVel (km/h)'].mean() == 50





def test_win2lin(solarsim_in):
    win2lin(solarsim_in)
    # the actual formating function is tested in test_Tecplot


def test_lin2win(solarsim_in):
    lin2win(solarsim_in)
    # the actual formating function is tested in test_Tecplot
