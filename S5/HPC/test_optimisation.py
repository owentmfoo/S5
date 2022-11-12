import pytest
from S5.HPC.optimisation import *
import numpy as np


def test_set_mean_const():
    x = np.linspace(1, np.pi*2, 101)
    y = np.array([1]*101)
    z = set_mean(x,10,x,4)
    assert z.mean() == 10

def test_set_mean_linear():
    x = np.linspace(0, np.pi * 2, 101)
    y = x*1.5
    z = set_mean(x,10,x,4)
    assert z.mean() == 10

def test_set_mean():
    x = np.linspace(0, np.pi * 2, 101)
    y = np.sin(x)
    z = set_mean(y,10,x,4)
    assert z.mean() == 10

def test_set_mean_clip_kph():
    x = np.linspace(0, np.pi * 2, 101)
    y = np.sin(x)*200
    z = set_mean(y,10,x,4,'kph')
    assert z.max() == 130
    assert z.min() == 10
    assert z.mean() == 10

def test_set_mean_clip_ms():
    x = np.linspace(0, np.pi * 2, 101)
    y = np.sin(x)*200
    z = set_mean(y,10,x,4,'ms')
    assert z.max() == 130/3.6
    assert z.min() == 10/3.6
    assert z.mean() == 10


def test_calc_strat_zero():
    x = np.linspace(0, np.pi * 2, 101)
    y = np.sin(x)
    z = calc_strat(y,0,10,x)
    assert z.mean() == 10
    assert z.max() == 10
    assert z.min() == 10

def test_calc_strat():
    x = np.linspace(0, np.pi * 2, 101)
    y = np.sin(x)
    z = calc_strat(y,1,10,x)
    assert z.mean() == 10
    assert z.max() == 11
    assert z.min() == 9