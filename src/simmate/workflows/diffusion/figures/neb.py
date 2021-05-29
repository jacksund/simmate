# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------------------


from simmate.configuration.django import setup_full  # ensures setup
from simmate.database.diffusion import Pathway as Pathway_DB

queryset = (
    Pathway_DB.objects.filter(
        vaspcalca__energy_barrier__isnull=False,
        vaspcalcb__energy_barrier__isnull=False,
        empiricalmeasures__ewald_energy__isnull=False,
    )
    .select_related("vaspcalca", "vaspcalcb", "empiricalmeasures", "structure")
    .all()
)
from django_pandas.io import read_frame

df = read_frame(
    queryset,
    fieldnames=[
        "id",
        "length",
        "atomic_fraction",
        "nsites_777",
        "nsites_101010",
        "structure__id",
        "structure__nsites",
        "structure__nelement",
        "structure__chemical_system",
        "structure__density",
        "structure__spacegroup",
        "structure__formula_full",
        "structure__formula_reduced",
        "structure__formula_anonymous",
        "structure__final_energy",
        "structure__final_energy_per_atom",
        "structure__formation_energy_per_atom",
        "structure__e_above_hull",
        "empiricalmeasures__oxidation_state",
        "empiricalmeasures__dimensionality",
        "empiricalmeasures__dimensionality_cumlengths",
        "empiricalmeasures__ewald_energy",
        "empiricalmeasures__ionic_radii_overlap_cations",
        "empiricalmeasures__ionic_radii_overlap_anions",
        "vaspcalca__energy_start",
        "vaspcalca__energy_midpoint",
        "vaspcalca__energy_end",
        "vaspcalca__energy_barrier",
        "vaspcalcb__energy_start",
        "vaspcalcb__energy_midpoint",
        "vaspcalcb__energy_end",
        "vaspcalcb__energy_barrier",
    ],
)

# --------------------------------------------------------------------------------------

# The code below is for interactive plotting using Plotly
# import plotly.express as px

# fig = px.scatter(
#     data_frame=df,
#     x="vaspcalca__energy_barrier",
#     y="vaspcalcb__energy_barrier",
#     color="empiricalmeasures__ewald_energy",
#     # text="structure__id",
#     hover_data=[
#         "id",
#         "length",
#         "structure__id",
#         "structure__formula_full",
#         "structure__spacegroup",
#         "structure__formula_anonymous",
#         "structure__e_above_hull",
#         "empiricalmeasures__ewald_energy",
#         "vaspcalca__energy_barrier",
#     ],
# )
# fig.show(renderer="browser", config={'scrollZoom': True})

# --------------------------------------------------------------------------------------

from sklearn import linear_model
from sklearn.model_selection import train_test_split

reg = linear_model.LinearRegression()
# reg = linear_model.Lasso(alpha=0.1)

# add one column
df["nsites_supercell_ratio"] = df["nsites_101010"] / df["nsites_777"]

# split our dataframe into training and test sets
# df_training, df_test = train_test_split(df, test_size=0.2)

# Fields to use in fitting
fields_to_fit = [
        # "id",
        "length",
        # "atomic_fraction",
        "nsites_777",
        # "nsites_101010",
        # "nsites_supercell_ratio",
        # "structure__id",
        # "structure__nsites",
        # "structure__nelement",
        # "structure__chemical_system",
        # "structure__density",
        # "structure__spacegroup",
        # "structure__formula_full",
        # "structure__formula_reduced",
        # "structure__formula_anonymous",
        # "structure__final_energy",
        # "structure__final_energy_per_atom",
        # "structure__formation_energy_per_atom",
        "structure__e_above_hull",
        # "empiricalmeasures__oxidation_state",
        # "empiricalmeasures__dimensionality",
        # "empiricalmeasures__dimensionality_cumlengths",
        "empiricalmeasures__ewald_energy",
        # "empiricalmeasures__ionic_radii_overlap_cations",
        # "empiricalmeasures__ionic_radii_overlap_anions",
        # "vaspcalca__energy_start",
        # "vaspcalca__energy_midpoint",
        # "vaspcalca__energy_end",
        "vaspcalca__energy_barrier",
        # "vaspcalcb__energy_start",
        # "vaspcalcb__energy_midpoint",
        # "vaspcalcb__energy_end",
        # "vaspcalcb__energy_barrier",
    ]

X_train = df[fields_to_fit]
y_train = df["vaspcalcb__energy_barrier"]
reg.fit(X_train,y_train)
coef = reg.coef_
r_2 = reg.score(X_train,y_train)
print(coef)
print(r_2)


# Now use our test set to see how the model does
X_test = df[fields_to_fit]
y_test_expected = df["vaspcalcb__energy_barrier"]
y_test_predicted = reg.predict(X_test)


# --------------------------------------------------------------------------------------


import matplotlib.pyplot as plt

# start with a square Figure
fig = plt.figure(figsize=(5, 5))  # golden ratio = 1.618

# Add axes for the main plot
ax = fig.add_subplot(
    xlabel=r"IDPP-relaxed Barrier (eV) [empirically corrected]",
    ylabel=r"Midpoint-only NEB Barrier (eV)",
    # xlim=(-0.5, 2.5),
    # ylim=(-0.5, 2.5),
)

# add the data as a scatter
hb = ax.scatter(
    x=y_test_predicted,  # X
    y=y_test_expected,  # Y
    c="Red",  # COLOR
    alpha=0.6,  # Transparency
)

# add a y=x line through the ploy
line = ax.plot(
    [-1, 1, 3],  # X
    [-1, 1, 3],  # Y
    c="Black",  # COLOR
)

plt.show()


# --------------------------------------------------------------------------------------


import matplotlib.pyplot as plt

# start with a square Figure
fig = plt.figure(figsize=(5, 5))  # golden ratio = 1.618

# Add axes for the main plot
ax = fig.add_subplot(
    xlabel=r"IDPP-relaxed Barrier (eV)",
    ylabel=r"Midpoint-only NEB Barrier (eV)",
    # xlim=(-0.5, 2.5),
    # ylim=(-0.5, 2.5),
)

# add the data as a scatter
hb = ax.scatter(
    x=df["vaspcalca__energy_barrier"],  # X
    y=df["vaspcalcb__energy_barrier"],  # Y
    c="Green",  # COLOR
    # alpha=0.6,  # Transparency
)

# hb = ax.scatter(
#     x=df["vaspcalca__energy_barrier"],  # X
#     y=y_test_predicted,  # Y
#     c="Blue",  # COLOR
#     # alpha=0.6,  # Transparency
# )

# add a y=x line through the ploy
line = ax.plot(
    [-1, 1, 3],  # X
    [-1, 1, 3],  # Y
    c="Black",  # COLOR
)

plt.show()


# --------------------------------------------------------------------------------------

test = y_test_expected - y_test_predicted
test.plot.hist("vaspcalcb__energy_barrier", bins=30)
