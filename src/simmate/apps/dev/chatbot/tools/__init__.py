from .basic import ask_general_question
from .molecules import get_add_hydrogens, get_inchi_key, get_num_rings, get_png_image
from .plotly import get_plotly_figure
from .simmate_db import get_answer_from_database, get_dataframe_from_database

# Combine all tools into a single list for use elsewhere
simmate_tools = [
    get_inchi_key,
    get_add_hydrogens,
    get_num_rings,
    get_png_image,
    get_plotly_figure,
    get_dataframe_from_database,
    get_answer_from_database,
    ask_general_question,
]
