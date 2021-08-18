# -*- coding: utf-8 -*-

"""
This script largely pulls from the CrystalToolKit code that is located on Github at 
https://github.com/materialsproject/crystaltoolkit/blob/master/crystal_toolkit/components/xrd.py

"""

##############################################################################

# IMPORTING STRUCTURE

from pymatgen import MPRester

MAPI_KEY = "2Tg7uUvaTAPHJQXl"  # Input your API key here! you can find it on the dashboard of the Materials Project website
mpr = MPRester(MAPI_KEY)
mp_id = "mp-2245"  # Input your structure of interest here!
struct = mpr.get_structure_by_material_id(mp_id)

##############################################################################

# CALCULATING DIFFRACTION PEAKS

from pymatgen.analysis.diffraction.xrd import XRDCalculator

XRDCalc = XRDCalculator(wavelength="CuKa", symprec=0, debye_waller_factors=None)

xrd_data = XRDCalc.get_pattern(
    struct, scaled=True, two_theta_range=None
)  # default two_theta_range = (0,90) # set to None for all

##############################################################################

# SIMULATING DIFFRACTION PATTERN BASED ON XRD-SOURCE, PARTICLE SIZE, AND CURVE TYPE

import math
import numpy as np
from scipy.special import wofz
from pymatgen.analysis.diffraction.xrd import (
    WAVELENGTHS,
)  # this is just a dictionary of values!


def G(x, c, alpha):
    """Return c-centered Gaussian line shape at x with HWHM alpha"""
    return (
        np.sqrt(np.log(2) / np.pi)
        / alpha
        * np.exp(-(((x - c) / alpha) ** 2) * np.log(2))
    )


def L(x, c, gamma):
    """Return c-centered Lorentzian line shape at x with HWHM gamma"""
    return gamma / (np.pi * ((x - c) ** 2 + gamma ** 2))


def V(x, c, alphagamma):
    """Return the c-centered Voigt line shape at x, scaled to match HWHM of Gaussian and Lorentzian profiles."""
    alpha = 0.61065 * alphagamma
    gamma = 0.61065 * alphagamma
    sigma = alpha / np.sqrt(2 * np.log(2))
    return np.real(wofz(((x - c) + 1j * gamma) / (sigma * np.sqrt(2)))) / (
        sigma * np.sqrt(2 * np.pi)
    )


def grain_to_hwhm(tau, two_theta, K=0.9, wavelength="CuKa"):
    """
    :param tau: grain size in nm
    :param theta: angle (in 2-theta)
    :param K: shape factor (default 0.9)
    :param wavelength: wavelength radiation in nm
    :return: half-width half-max (alpha or gamma), for line profile
    """
    wavelength = WAVELENGTHS[wavelength]
    return (
        0.5 * K * 0.1 * wavelength / (tau * abs(np.cos(two_theta / 2)))
    )  # Scherrer equation for half-width half max


def XRDsimulatespectra(
    xrd_data=None, logsize=1, rad_source="CuKa", peak_profile="Gaussian", K=0.9
):

    x_peak = xrd_data.x
    y_peak = xrd_data.y
    grain_size = (
        10 ** logsize
    )  # size of the grains in nm --> so 0.1nm grain size has a logsize=-1

    num_sigma = {"Gaussian": 5, "Lorentzian": 12, "Voigt": 12}[peak_profile]

    # optimal number of points per degree determined through usage experiments
    if logsize > 1:
        N_density = 150 * (logsize ** 4)  # scaled to log size to the 4th power
    else:
        N_density = 150

    # start with a flat line of points and we will add cumulative peaks to it
    first_peak = x_peak[0]
    last_peak = x_peak[-1]
    domain = last_peak - first_peak  # find total domain of angles in pattern
    N = int(N_density * domain)  # num total points
    x = np.linspace(first_peak, last_peak, N).tolist()
    y = np.zeros(len(x)).tolist()

    for xp, yp in zip(x_peak, y_peak):
        alpha = grain_to_hwhm(
            tau=grain_size,
            two_theta=math.radians(xp / 2),
            K=float(K),
            wavelength=rad_source,
        )
        sigma = (alpha / np.sqrt(2 * np.log(2))).item()

        center_idx = int(round((xp - first_peak) * N_density))
        half_window = int(
            round(num_sigma * sigma * N_density)
        )  # i.e. total window of 2 * num_sigma

        lb = max([0, (center_idx - half_window)])
        ub = min([N, (center_idx + half_window)])

        if peak_profile == "Gaussian":
            G0 = G(x=0, c=0, alpha=alpha)
            for i, j in zip(range(lb, ub), range(lb, ub)):
                y[j] += yp * G(x[i], xp, alpha) / G0

        elif peak_profile == "Lorentzian":
            G0 = L(x=0, c=0, gamma=alpha)
            for i, j in zip(range(lb, ub), range(lb, ub)):
                y[j] += yp * L(x[i], xp, alpha) / G0

        elif peak_profile == "Voigt":
            G0 = V(x=0, c=0, alphagamma=alpha)
            for i, j in zip(range(lb, ub), range(lb, ub)):
                y[j] += yp * V(x[i], xp, alpha) / G0

    return {"x": x, "y": y}


# # run the above code
# xrd_data_simulated = XRDsimulatespectra(xrd_data=xrd_data,
#                                         logsize=0,
#                                         rad_source="CuKa",
#                                         peak_profile="Voigt", # Gaussian, Lorentzian, or Voigt
#                                         K=0.94)

# import pandas as pd
# df = pd.DataFrame(xrd_data_simulated)

##############################################################################

# Simmulate a range of crystallite sizes

sizes_to_test = [math.log10(size) for size in [0.005, 0.01, 0.02, 0.1, 0.2, 1]]

all_size_data = [
    XRDsimulatespectra(
        xrd_data=xrd_data, logsize=size, rad_source="CuKa", peak_profile="Voigt", K=0.94
    )
    for size in sizes_to_test
]

d = {
    "0.005x": all_size_data[0]["x"],
    "0.005y": all_size_data[0]["y"],
    "0.01x": all_size_data[1]["x"],
    "0.01y": all_size_data[1]["y"],
    "0.02x": all_size_data[2]["x"],
    "0.02y": all_size_data[2]["y"],
    "0.1x": all_size_data[3]["x"],
    "0.1y": all_size_data[3]["y"],
    "0.2x": all_size_data[4]["x"],
    "0.2y": all_size_data[4]["y"],
    "1x": all_size_data[5]["x"],
    "1y": all_size_data[5]["y"],
}

import pandas as pd

df = pd.DataFrame(d)

# add random noise to each spectra
x_vals = np.array(all_size_data[0]["x"])
noise1 = np.random.normal(0, 10, len(x_vals)) * np.sin(x_vals * 8)
noise2 = np.random.normal(0, 9, len(x_vals)) * np.sin(x_vals * 8)
noise3 = np.random.normal(0, 5, len(x_vals)) * np.sin(x_vals * 10)
noise4 = np.random.normal(0, 3, len(x_vals)) * np.sin(x_vals * 15)
noise5 = np.random.normal(0, 2, len(x_vals)) * np.sin(x_vals * 20)
noise6 = np.random.normal(0, 1, len(x_vals)) * np.sin(x_vals * 50)

##############################################################################

# PLOTTING THE RESULTS

import plotly.graph_objects as go
from plotly.offline import plot


# series1 = go.Bar(name='XRD',
#                  x=xrd_data.x,
#                  y=xrd_data.y,
#                  width=1,
#                  )

# series2 = go.Scatter(name='XRD',
#                      x=xrd_data_simulated['x'],
#                      y=xrd_data_simulated['y'],
#                      mode='lines', # lines, markers, text, (or a combo like lines+marker)
#                      marker=dict(size=12,
#                                  color='rgba(0, 0, 0, 0.8)',),
#                      text=[entry[0]['hkl'] for entry in xrd_data.hkls],
#                     )

### All cryst sizes ###

series3 = go.Scatter(
    name="0.005nm",
    x=df["0.005x"],
    y=df["0.005y"] + noise1,
    mode="lines",  # lines, markers, text, (or a combo like lines+marker)
    marker=dict(
        size=12,
        color="rgba(255, 0, 0, 1)",
    ),
    text=[entry[0]["hkl"] for entry in xrd_data.hkls],
)

series4 = go.Scatter(
    name="0.01nm",
    x=df["0.01x"],
    y=df["0.01y"] + noise2,
    mode="lines",  # lines, markers, text, (or a combo like lines+marker)
    marker=dict(
        size=12,
        color="rgba(255, 0, 255, 1)",
    ),
    text=[entry[0]["hkl"] for entry in xrd_data.hkls],
)

series5 = go.Scatter(
    name="0.02nm",
    x=df["0.02x"],
    y=df["0.02y"] + noise3,
    mode="lines",  # lines, markers, text, (or a combo like lines+marker)
    marker=dict(
        size=12,
        color="rgba(0, 0, 0, 1)",
    ),
    text=[entry[0]["hkl"] for entry in xrd_data.hkls],
)

series6 = go.Scatter(
    name="0.1nm",
    x=df["0.1x"],
    y=df["0.1y"] + noise4,
    mode="lines",  # lines, markers, text, (or a combo like lines+marker)
    marker=dict(
        size=12,
        color="rgba(0, 255, 0, 1)",
    ),
    text=[entry[0]["hkl"] for entry in xrd_data.hkls],
)

series7 = go.Scatter(
    name="0.2nm",
    x=df["0.2x"],
    y=df["0.2y"] + noise5,
    mode="lines",  # lines, markers, text, (or a combo like lines+marker)
    marker=dict(
        size=12,
        color="rgba(0, 0, 0, 1)",
    ),
    text=[entry[0]["hkl"] for entry in xrd_data.hkls],
)

series8 = go.Scatter(
    name="1nm",
    x=df["1x"],
    y=df["1y"] + noise6,
    mode="lines",  # lines, markers, text, (or a combo like lines+marker)
    marker=dict(
        size=12,
        color="rgba(0, 0, 255, 1)",
    ),
    text=[entry[0]["hkl"] for entry in xrd_data.hkls],
)

### END All cryst sizes ###

layout = go.Layout(
    width=500 * 10 / 9,  # golden = 1.6180339887498948482
    height=500,
    plot_bgcolor="white",
    paper_bgcolor="white",
    xaxis=dict(
        title_text="Raman shift (cm<sup>-2</sup>)",
        range=[15, 75],
        showgrid=False,
        zeroline=False,
        ticks="outside",
        tickwidth=2,
        showline=True,
        color="black",
        linecolor="black",
        linewidth=2,
        mirror=True,
        # dtick=250,
        tick0=1000,
    ),
    yaxis=dict(
        title_text="Intensity (a.u.)",
        # range=[0,75],
        showgrid=False,
        zeroline=False,
        ticks="",  # 'outside', 'inside', ''
        tickwidth=2,
        showline=True,
        showticklabels=False,
        linewidth=2,
        color="black",
        linecolor="black",
        mirror=True,
        # dtick=25000,
        tick0=0,
    ),
    legend=dict(
        x=0.05,
        y=0.95,
        bordercolor="black",
        borderwidth=1,
        font=dict(color="black"),
    ),
)

fig = go.Figure(
    data=[series3, series4, series5, series6, series7, series8], layout=layout
)

# save as an html file and open with Chromium
plot(fig, config={"scrollZoom": True})


# save as an svg file # GIVES AN ERROR RIGHT NOW -- this should be easier
# import plotly
# plotly.io.orca.config.executable = '/home/jacksund/anaconda3/envs/jacks_env/bin/orca'
# fig.write_image("/home/jacksund/Documents/Spyder/graphene-fig-data.svg")
