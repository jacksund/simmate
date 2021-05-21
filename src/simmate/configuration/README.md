This module is empty at the moment, but I plan for it to be for setting up the program (or maybe I have a setup module with each other module, such as website.setup and database.setup...?). Either way, I will likely save a /.simmate folder to the user's home directory that helps configure lots of settings -- such as the location of bader.exe or POTCAR files. I could also add a script that prompts user input to set this up right from the start.

To get Plotly working in spyder:

# override the default
import plotly.io as pio
pio.renderers.default='browser'

# or change the renderer temporarily
fig.show(renderer="browser")