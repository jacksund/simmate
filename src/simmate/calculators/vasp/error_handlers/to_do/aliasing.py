# -*- coding: utf-8 -*-

from pathlib import Path

from simmate.calculators.vasp.inputs import Incar
from simmate.workflow_engine import ErrorHandler


class Aliasing(ErrorHandler):
    """
    Aliasing errors occur when there are issues with the NGX, NGY, and NGZ grid
    in VASP. Typically the fix is to just remove user defined settings for these
    values, delete the CHGCAR and WAVECAR, and then restart the calculation. In
    some cases, VASP even provides recommended values for this grid and we just
    use those.
    """

    # run this while the VASP calculation is still going
    is_monitor = True

    # These are the error messages that we are looking for
    possible_error_messages = {
        "aliasing_error": "WARNING: small aliasing (wrap around) errors must be expected",
        "insufficient_fft_grid": "Your FFT grids (NGX,NGY,NGZ) are not sufficient for an accurate",
    }

    # All instances of this ErrorHandler will work exactly the same, so there
    # are no keywords available -- and also there's no need for a __init__()

    def correct(self, directory: Path) -> str:
        """
        Perform corrections based on the INCAR.
        """

        raise NotImplementedError("This handler has not been ported from custodian yet")

        # Note "error" here is a list of the errors found. For example, error
        # could be ["alaising_error", "insufficient_fft_grid"]. If there
        # weren't any errors found then this is just and empty list.

        # Multiple corrections could be applied here so we record all of them.
        corrections = []

        # load the INCAR file to view the current settings
        incar_filename = directory / "INCAR"
        incar = Incar.from_file(incar_filename)

        if "aliasing" in error:

            # VASP will actually tell us what to switch NGX, NGY, and NGZ to inside
            # the OUTCAR. So we look there for our fix.
            # Here is what the aliasing error typically looks like in the OUTCAR:
            #   WARNING: aliasing errors must be expected set NGX to  34 to avoid them
            #   NGY is ok and might be reduce to 102
            #   NGZ is ok and might be reduce to 120
            #   aliasing errors are usually negligible using standard VASP settings
            #   and one can safely disregard these warnings

            # so we open the OUTCAR and find these lines and the suggested fix.

            # read the file content and then close it
            outcar_filename = directory / "OUTCAR"
            with outcar_filename.open() as file:
                outcar_lines = file.readlines()

            # go through each line looking for the suggestions
            for line in outcar_lines:
                if "to avoid them" in line:

                    # break the line up into a list, where NG* is at index 7 and
                    # the fix is at index 9.
                    # BUG: I expect an error will show up here if I was wrong about
                    # the indexes of what we want always being 7 and 9.
                    line_info = line.split()
                    incar_key = line_info[7]
                    new_value = int(line_info[9])

                    # update the incar with this value
                    incar.update({incar_key: new_value})

                    # record the correction
                    corrections.append(f"switched {incar_key} to {new_value}")

        if "insufficient_fft_grid" in error:

            # This is typically caused by a user introducing too coarse of a grid.
            # Here we remove all NGX/NGY/NGZ settings from the INCAR
            incar.pop("NGX")
            incar.pop("NGY")
            incar.pop("NGZ")
            # record the change
            corrections.append("removed all NGX/NGY/NGZ settings")

        # if any corrections were made above, we may want to reset some files
        if corrections:

            # Check the current ICHARG setting, where default is 0
            # !!! BUG: isn't the default 2 if we are starting from scratch?
            current_icharg = incar.get("ICHARG", 0)

            # If the ICHARG is less than 10, then we want to delete the CHGCAR
            # and WAVECAR to ensure the next run is a clean start.
            if current_icharg < 10:
                (directory / "CHGCAR").unlink()
                (directory / "WAVECAR").unlink()

            # return the description of what we did
            corrections.append("deleted CHGCAR and WAVECAR")

        # rewrite the new INCAR file
        incar.to_file(incar_filename)

        # return the list of corrections we made
        return corrections
