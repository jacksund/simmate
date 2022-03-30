# -*- coding: utf-8 -*-

import os
import pytest
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


class IncorrectHandler(ErrorHandler):
    # filename_to_check  # <-- incorrectly missing this field
    # possible_error_messages <-- incorrectly missing this field

    def correct(self, directory):
        return "ExampleCorrection"


def test_error_handler():

    directory = os.path.dirname(__file__)

    # test basic use
    handler = CheckREADME()
    assert handler.check(directory=directory)
    assert handler.correct(directory=directory) == "ExampleCorrection"

    # confirm Exception when settings are improperly set
    handler = IncorrectHandler()
    with pytest.raises(Exception):
        handler.check(directory=directory)

    # This line tests nothing, but simply covers the abstract method's pass statement
    ErrorHandler.correct(None, None)
