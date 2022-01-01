# -*- coding: utf-8 -*-

import os

from simmate.workflow_engine.error_handler import ErrorHandler


class CheckREADME(ErrorHandler):
    """
    This checks if simmate is in located in this file (which will always be true).

    This is just to check the default check() method for the ErrorHandler class.
    """

    filename_to_check = __file__
    possible_error_messages = ["simmate"]

    def correct(self, directory):
        return "ExampleCorrection"


def test_error_handler():

    handler = CheckREADME()

    assert handler.check(directory=os.path.dirname(__file__))
