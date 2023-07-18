# -*- coding: utf-8 -*-

from simmate.utilities import bypass_nones


def test_bypass_nones():
    values_in = ["abcdefg", None, None, "abcdefg", None, "abcdefg", None, None]
    expected_out = [7, None, None, 7, None, 7, None, None]

    # EXAMPLE 1-----------------------
    @bypass_nones(bypass_kwarg="values")
    def get_lens(values):
        return [len(v) for v in values]

    values_out = get_lens(values=values_in)
    assert values_out == expected_out

    # EXAMPLE 2------------------------
    def get_lens(values):
        return [len(v) for v in values]

    get_lens_cleaned = bypass_nones(bypass_kwarg="values")(get_lens)

    values_out = get_lens_cleaned(values=values_in)
    assert values_out == expected_out

    # EXAMPLE 3-----------------------
    @bypass_nones(bypass_kwarg="values", multi_cols=True)
    def get_lens_dup(values):
        lens = [len(v) for v in values]
        return lens, lens, lens

    values_out = get_lens_dup(values=values_in)
    assert values_out == [expected_out, expected_out, expected_out]
