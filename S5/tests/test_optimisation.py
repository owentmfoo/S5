import random

import pytest
from S5.HPC.optimisation import *
import numpy as np
from pytest import approx


def test_set_mean_const():
    x = np.linspace(1, np.pi * 2, 101)
    y = np.array([1] * 101)
    z = set_mean(x, 10, x, 4)
    assert z.mean() == approx(10)


def test_set_mean_linear():
    x = np.linspace(0, 10, 101)
    z = set_mean(x, 10, x, 4)
    assert z.mean() == approx(10)
    assert np.allclose(np.linspace(5,15,101),z)


def test_set_mean():
    x = np.linspace(0, np.pi * 2, 101)
    y = np.sin(x)
    z = set_mean(y, 10, x, 4)
    assert z.mean() == approx(10)

def test_set_mean_clip_kph_lin():
    x = np.linspace(0, 10, 101)
    y = x.copy()
    y[random.randint(0, 100)] = 100
    z = set_mean(y, 70, x, 8, 'kph')
    assert np.trapz(z, x) / (x.max() - x.min()) == approx(70)
    assert z.max() == approx(130)


def test_set_mean_clip_kph():
    x = np.linspace(0, np.pi * 2, 101)
    y = np.sin(x) * 200
    v_bar = random.randint(40,100)
    z = set_mean(y, v_bar, x, 8, 'kph')
    assert z.max() == approx(130)
    assert z.min() == approx(10)
    assert np.trapz(z, x) / (x.max() - x.min()) == approx(v_bar)


def test_set_mean_clip_ms():
    x = np.linspace(0, np.pi * 2, 101)
    y = np.sin(x) * 200
    v_bar = random.randint(10, 27)
    z = set_mean(y, v_bar, x, 8, 'ms')
    assert z.max() == approx(130 / 3.6)
    assert z.min() == approx(10 / 3.6)
    assert np.trapz(z, x) / (x.max() - x.min()) == approx(v_bar)


def test_calc_strat_zero():
    x = np.linspace(0, np.pi * 2, 101)
    y = np.sin(x)
    z = calc_strat(y, 0, 10, x)
    assert z.mean() == approx(10)
    assert z.max() == approx(10)
    assert z.min() == approx(10)


def test_calc_strat():
    x = np.linspace(0, np.pi * 2, 101)
    y = np.sin(x)
    z = calc_strat(y, 1, 10, x)
    assert z.mean() == approx(10)
    assert np.percentile(z, 68) == approx(11)
    assert np.percentile(z, 32) == approx(9)

#TODO: add tests with real data