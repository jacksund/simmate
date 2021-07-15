# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------------------

from simmate.configuration.django import setup_full  # ensures setup
from simmate.database.diffusion import Pathway as Pathway_DB

queryset = (
    Pathway_DB.objects.filter(
        vaspcalcb__energy_barrier__isnull=False,
    )
    .select_related("structure")
    # .order_by("structure__id")
    .distinct("structure__id")
    .all()
)
from django_pandas.io import read_frame

df = read_frame(
    queryset,
    fieldnames=["id", "structure__nelement",],
)

# This gives us counts for a pie/bar chart
df_counts = df["structure__nelement"].value_counts()

# --------------------------------------------------------------------------------------

import matplotlib.pyplot as plt

fig1, ax1 = plt.subplots()
ax1.pie(
    df_counts,
    labels=["ternary", "quaternary", "binary", "quinary"],
    autopct="%1.1f%%",
    startangle=90,
)
ax1.axis("equal")  # Equal aspect ratio ensures that pie is drawn as a circle.

plt.show()
# plt.savefig('test.png', dpi = 1000)

# --------------------------------------------------------------------------------------
