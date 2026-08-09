# -*- coding: utf-8 -*-


def validate_cas_number(cas_number: str) -> bool:
    """
    The final number in CAS numbers have are actually a check digit, which
    can help verify if you have a legitamate CAS number.

    This method check to see if the CAS number passes the "valid" check
    and is necessary when using third-party sources such as PubChem.

    Read more about validation at:
    https://www.cas.org/support/documentation/chemical-substances/checkdig
    """
    # "A CAS Registry Number includes up to 10 digits which are separated
    # into 3 groups by hyphens. The first part of the number, starting from
    # the left, has 2 to 7 digits; the second part has 2 digits. The final
    # part consists of a single check digit.
    chunks = cas_number.split("-")

    # check 1: must have 3 sections
    if len(chunks) != 3:
        return False  # FAILS

    # check 2: each section must be numerical and an integer
    try:
        primary, secondary, check_digit = [int(c) for c in chunks]
    except:
        return False  # FAILS

    # check 3: secondary digit must be 2 digits (i.e. under 100)
    if secondary >= 100:
        return False
    # if the secondary value is 1-9, then we need a leading zero. which is why
    # we format the string below

    # check 4: final section must be 1 number
    if check_digit >= 10:
        return False  # FAILS

    # check 4: make sure check_digit is expected value. See the formula at...
    #   https://www.cas.org/support/documentation/chemical-substances/checkdig
    rn_flat = str(primary) + f"{secondary:02d}"
    expected_check_digit = (
        sum([(len(rn_flat) - n) * int(i) for n, i in enumerate(rn_flat)]) % 10
    )
    if check_digit != expected_check_digit:
        return False

    # if all checks above passed
    return True
