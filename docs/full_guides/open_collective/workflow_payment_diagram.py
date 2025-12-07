# -*- coding: utf-8 -*-

import plotly.graph_objects as go

# ---------------------------------------------
# 0. Color Reference Dictionary (from colorway)
# ---------------------------------------------

color_ref = {
    "green": "rgba(16, 196, 105, 1.0)",
    "blue": "rgba(4, 144, 204, 1.0)",
    "yellow": "rgba(249, 200, 81, 1.0)",
    "black": "rgba(0, 0, 0, 1.0)", 
    "red": "rgba(255, 91, 91, 1.0)",
    "light_blue": "rgba(143, 205, 255, 1.0)",
    "light_grey": "rgba(200, 200, 200, 1.0)",
    "dark_grey": "rgba(100, 100, 100, 1.0)",
}

# ----------------------------------------------------
# 1. Configuration Dictionary
# ----------------------------------------------------
w = 85  # worker
t = 5 # treasury
v = 10 # validator

w_b = 0.97  # worker bank account
w_f = 0.03  # transfer fees

t_c = 0.75  # treasury to cloud
t_d = 0.2   # treasury to development
t_p = 0.05  # treasury to promotions

sankey_config = {
    "nodes": [
        ["User Wallet", color_ref["blue"], 0.0, 0.45], # 0
        ["Simmate Escrow", color_ref["green"], 0.33, 0.55], # 1 
        ["Worker Wallet", color_ref["light_grey"], 0.66, 0.4], # 2
        ["Worker Bank Account", color_ref["black"], 1.0, 0.35], # 3
        ["Bank Transfer Fees", color_ref["black"], 1.0, 0.76], # 4
        ["Simmate Treasury", color_ref["yellow"], 0.66, 0.85], # 5
        ["Validator Pool", color_ref["red"], 0.66, 0.95], # 6
        ["Cloud Costs", color_ref["yellow"], 1.0, 0.80], # 7
        ["Development", color_ref["yellow"], 1.0, 0.83], # 8
        ["Promotions & Incentives", color_ref["yellow"], 1.0, 0.85], # 9
        ["Validator Wallet 1", color_ref["red"], 1.0, 0.88], # 10
        ["Validator Wallet 2", color_ref["red"], 1.0, 0.92],# 11
        ["Validator Wallet 3", color_ref["red"], 1.0, 0.96], # 12
        ["Validator Wallet N", color_ref["red"], 1.0, 1.0], # 13
    ],
    "links": [
        [0, 1, 100, "Transfer (workflow is submitted)"],
        [1, 2, w, "Worker Payout"],
        [1, 5, t, "Simmate Treasury Fee"],
        [1, 6, v, "Validator Fee"],
        # Worker Wallet
        [2, 3, w*w_b, "Worker Bank Account"],
        [2, 4, w*w_f, "Bank Transfer Fees"],
        # Existing Treasury + Validator links
        [5, 7, t*t_c, "Cloud Costs"],
        [5, 8, t*t_d, "Development"],
        [5, 9, t*t_p, "Promotions & Incentives"],
        [6, 10, v/4, "Validator Payout"],
        [6, 11, v/4, "Validator Payout"],
        [6, 12, v/4, "Validator Payout"],
        [6, 13, v/4, "Validator Payout"],
    ]
}

# ----------------------------------------------------
# 2. Process Configuration
# ----------------------------------------------------
LINK_ALPHA = 0.4

node_labels = [n[0] for n in sankey_config["nodes"]]
node_rgba_colors = [n[1] for n in sankey_config["nodes"]]
node_x_pos = [n[2] for n in sankey_config["nodes"]]
node_y_pos = [n[3] for n in sankey_config["nodes"]]

# Extract RGB for link transparency
node_rgb_values = []
for rgba in node_rgba_colors:
    rgb_str = rgba.split("(")[1].split(", 1.0)")[0]
    node_rgb_values.append(rgb_str)

source = [l[0] for l in sankey_config["links"]]
target = [l[1] for l in sankey_config["links"]]
value = [l[2] for l in sankey_config["links"]]
label_text = [l[3] for l in sankey_config["links"]]

link_colors_rgba = [f"rgba({node_rgb_values[s]}, {LINK_ALPHA})" for s in source]

# ----------------------------------------------------
# 3. Build Figure
# ----------------------------------------------------
fig = go.Figure(data=[go.Sankey(
    node=dict(
        pad=15,
        thickness=20,
        line=dict(color="black", width=0.5),
        label=node_labels,
        color=node_rgba_colors,
        x=node_x_pos,
        y=node_y_pos,
        hoverinfo='none',
        # Larger label font size
        # hoverfont=dict(size=20),
        # font=dict(size=20)  # <-- main node label font size
    ),
    link=dict(
        source=source,
        target=target,
        value=value,
        label=label_text,
        color=link_colors_rgba,
        hoverinfo='none',
        # Make link labels visible
        # hovertemplate='%{label}<extra></extra>'
    )
)])

fig.update_layout(
    title_text="Where funds go when a user submits a workflow",
    font_size=30,
)

fig.show(renderer="browser")
