import S5.Tecplot as TP
import warnings
import numpy as np
import math


def calc_strat_new(driver, c, v_bar, x, clip=None):
    '''scale the target velocity to c with mean v_bar and profile driver'''
    n = 8
    if c == 0:
        v_bar = round(v_bar, n)
        velout = driver * 0 + v_bar
        return velout
    r = extract_prime(driver, x, n)  # extract variation
    # print(np.percentile(r,95),max(r))
    adj = r / np.percentile(r, 68) * c  # normalise the magnitude
    vel = v_bar + adj  # adjust the mean value
    return set_mean(vel, v_bar, x, n, clip)


def set_mean(vel, v_bar, x, n, clip=None):
    '''adjust the mean velocity recursively
    :param vel: array of velocity
    :param v_bar: target mean velocity
    :param x: distnance correcponding to the velocity points
    :param n: precision in decimal points
    :param clip: clipping to reduce spikes, None, "kph", or "ms"
    '''
    velout = 'spam'
    vel = np.copy(v_bar + vel - np.trapz(vel, x) / (x.max() - x.min()))
    if clip is None:
        velout = vel
    elif clip == "kph":
        clip_max = 130
        clip_min = 10
        velout = np.clip(vel, clip_max, clip_min)
    elif clip == "ms":
        clip_max = 130 / 3.6
        clip_min = 10 / 3.6
        velout = np.copy(np.clip(vel, clip_max, clip_min))
    # elif isinstance(clip,dict): # this was in alpha but not used
    #     if "road" in clip:
    #         roadfile = clip["road"]
    #         roadTP = TP.Tecplot(roadfile)
    #         roadTP.data.set_index("Distance (km)",inplace=True)
    #         velDF = None
    #
    else:
        velout = vel
        warnings.warn("clip specifier not valid, no clip is applied.")

    if np.isclose(np.trapz(velout, x) / (x.max() - x.min()), v_bar):
        return velout.copy()
    # else:
    #     try:
    #         velout = set_mean(np.copy(vel), v_bar, x, min(n - 0.002, 4),clip) # python recursion limit is 1000
    #     except RecursionError:
    #         warnings.warn(f'max recursion reached with v_bar = {v_bar}')
    #     return velout.copy()
    velout = _set_mean_clip_optifun(vel, v_bar, x, n, clip=clip)
    current_delta = np.trapz(velout, x) / (x.max() - x.min()) - v_bar  # detla is positive if the actual is larger
    # than the target
    adjust = v_bar - current_delta  # if the actual is larger than target, take some off
    while not math.isclose(current_delta, 0, abs_tol=1e-12):
        velout = _set_mean_clip_optifun(vel, v_bar + adjust, x, n, clip=clip)
        current_delta = np.trapz(velout, x) / (x.max() - x.min()) - v_bar
        adjust -= current_delta

    # v_bar = v_bar + adjust
    # vel = np.copy(v_bar + vel - np.trapz(vel, x) / (x.max() - x.min()))
    # if clip == "kph":
    #     velout = np.clip(vel, 10, 130)
    # elif clip == "ms":
    #     velout = np.copy(np.clip(vel, 10 / 3.6, 130 / 3.6))
    return velout


def _set_mean_clip_optifun(vel, v_bar, x, n, clip=None):
    '''adjust the mean velocity recursively
    :param vel: array of velocity
    :param v_bar: target mean velocity
    :param x: distnance correcponding to the velocity points
    :param n: precision in decimal points
    :param clip: clipping to reduce spikes, None, "kph", or "ms"
    '''
    velout = 'spam'
    vel = np.copy(v_bar + vel - np.trapz(vel, x) / (x.max() - x.min()))
    if clip is None:
        velout = vel
    elif clip == "kph":
        velout = np.clip(vel, 10, 130)
    elif clip == "ms":
        velout = np.copy(np.clip(vel, 10 / 3.6, 130 / 3.6))
    else:
        velout = vel
        warnings.warn("clip specifier not valid, no clip is applied.")
    return velout


def extract_prime(vel, x, n):
    v_prime = vel - np.trapz(vel, x) / (x.max() - x.min())
    assert round(np.trapz(v_prime, x), round(n)) == 0
    return v_prime
    # else:
    #     try:
    #         return extract_prime(v_prime, x, n - 0.0005)
    #     except RecursionError:
    #         warnings.warn(f'max recursion reached for extract_prime')
    #         return v_prime


def calc_strat(driver, c, v_bar, x, clip=None):
    return calc_strat_new(driver, c, v_bar, x, clip)
    # r = driver - np.trapz(driver,x)/(x.max()-x.min()) #extract variation
    # adj = r/np.max(r)*c #normalise the magnitude
    # vel = v_bar-np.trapz(adj,x)/(x.max()-x.min()) + adj # adjust the mean value
    # n=5
    # while np.round((x.max()-x.min())/np.trapz(1/vel, x),round(n)) != np.round(v_bar,round(n)):
    #     vel = v_bar-(x.max()-x.min())/np.trapz(1/vel, x)+vel
    #     n = max([abs(n-0.001),2])
    # return vel
