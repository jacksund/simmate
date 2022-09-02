# -*- coding: utf-8 -*-

from simmate.workflow_engine import S3Workflow


class PopulationAnalysis__Bader__Bader(S3Workflow):

    required_files = ["CHGCAR_sum", "POTCAR"]
    use_database = False

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
    you will see files like "CHGCAR_empty" used in the command.
    """
