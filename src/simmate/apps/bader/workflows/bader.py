# -*- coding: utf-8 -*-

from simmate.engine import S3Workflow
from simmate.apps.badelf.core import Grid


class PopulationAnalysis__Bader__Bader(S3Workflow):
    required_files = ["AECCAR0", "AECCAR2", "CHGCAR", "POTCAR"]
    use_database = False
    use_previous_directory = ["AECCAR0", "AECCAR2", "CHGCAR", "POTCAR"]
    parent_workflows = ["population-analysis.vasp-bader.bader-matproj"]

    command = "bader CHGCAR -ref CHGCAR_sum -b weight > bader.out"
    """
    The command to call the executable, which is typically bader. Note we
    use the `-b weight` by default, which means we apply the weight method for
    partitioning from of 
    [Yu and Trinkle](http://theory.cm.utexas.edu/henkelman/code/bader/download/yu11_064111.pdf).
    
    This command is modified to use the `-ref` file as the reference for determining
    zero-flux surfaces when partitioning the CHGCAR. 
    
    There are cases where also use structures that contain "empty atoms" in them.
    This is to help with partitioning of electrides, which possess electron 
    density that is not associated with any atomic orbital. For these cases,
    you will see files like "CHGCAR_w_empty_atoms" used in the command.
    """
    
    @staticmethod
    def setup(directory):
        """
        The henkelman bader algorithm uses the total charge density as a reference
        file. VASP returns the core electrons and valence electrons in seperate
        files which must be summed together to create this reference file. This
        setup method performs this action and writes the necessary file
        """
        aeccar0 = Grid.from_file(directory / "AECCAR0")
        aeccar2 = Grid.from_file(directory / "AECCAR2")
        chgcar_sum = Grid.sum_grids(aeccar0, aeccar2)
        chgcar_sum.write_file(directory / "CHGCAR_sum")