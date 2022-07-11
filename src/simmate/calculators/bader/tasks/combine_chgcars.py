# -*- coding: utf-8 -*-

from simmate.workflow_engine import S3Task


# TODO: The chgsum.pl script will be replaced with a simple python function
# that just sums the two files. It might not be as fast but it removes one
# executable file from having to be in the user's path. So in the future, this
# Task will be depreciated/removed into the BaderAnalysis.setup method.
class CombineCHGCARs(S3Task):
    """
    This tasks simply sums two charge density files into a new file. It uses
    a script from the Henkleman group.
    """

    command = "chgsum.pl AECCAR0 AECCAR2 > chgsum.out"
    monitor = False
    required_files = ["CHGCAR", "AECCAR0", "AECCAR2"]
