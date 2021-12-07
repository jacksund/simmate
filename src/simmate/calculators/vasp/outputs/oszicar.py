# -*- coding: utf-8 -*-

# !!! In the future, I think this should be a "converter" class that loads data
# into a more generic DftResults class -- so one that is more generically for
# storing electronic and ionic steps across different calculators. I think it
# would be useful to have a ElectronicStep and IonicStep classes.

import numpy


class Oszicar:
    """
    Reads all data from an OSZICAR file. This includes data on each electronic
    and ionic step of the calculation.

    Note that this class is only used when the speed of file-reading is important.
    If you are trying to analyze your VASP run, you should instead use the VaspXML
    output, which gives all of the information already in the OSZICAR and more!

    To help with understanding the OSZICAR file, you can also look here:
        https://www.vasp.at/wiki/index.php/OSZICAR
    """

    def __init__(self, filename="OSZICAR"):

        # Make an empty list to store all of the ionic steps. While relaxations
        # have many ionic steps, note that a static energy calculation will only
        # ever have one step. Either way, we still store the steps in a list.
        self.ionic_steps = []

        # open the file, read it's contents, and close immediately
        with open(filename) as file:
            lines = file.readlines()
        # Empty lines cause trouble so we remove those before parsing any data.
        lines = [line for line in lines if line.strip()]

        # now let's iterate through the contents and parse the data. We also need
        # to check the line number below, so we use the index too
        for line_number, line in enumerate(lines):

            # if "N" is in the line, that means we have the start of a new ionic step
            if "N" in line:

                # let's start with an empty list to record all of the electronic
                # steps. Note this will also reset the list every time we start
                # a new ionic step.
                electronic_steps = []
            # if "F" is in the line, that means we have hit the end of an ionic step.
            # We also need to account for when the calculation is not finished and
            # in the middle of an ionic step. Therefore we also check if this is the final
            # line of the file.
            elif "F" in line:

                # parse this line to pull out the ionic_step information
                # The formatting is whacky, so I decided to remove all variable
                # names, leaving only a list of values. I then split these values
                # into a list that I can more easily work with.
                values = (
                    line.strip()
                    .replace("T= ", "")
                    .replace("E= ", "")
                    .replace("F= ", "")
                    .replace("E0= ", "")
                    .replace("d E =", "")
                    .replace("mag=", "")
                    .replace("EK=", "")
                    .replace("SP=", "")
                    .replace("SK=", "")
                    .split()
                )

                # convert the list of strings to float values. We skip the first
                # value which is just the ionic_step_number that we don't need
                values = [float(value) for value in values[1:]]

                # Now there are three formats that we need to account for, which
                # each have a different amount of information given, and we can
                # figure out the type easy based on the length of our list of
                # values. These are...
                #   (1) non-magnetic calculations (F, E0, dE)
                #   (2) molecular dynamics calculations (T, E, F, E0, EK, SP, SK)
                # Further, magnetic calculations will have another value added
                # on at the end (mag). We account for this below too.

                # check if we have a simple energy calculation
                if len(values) in [3, 4]:
                    ionic_step = {
                        "energy": values[0],  # F (total_free_energy)
                        "energy_sigma_zero": values[1],  # E0
                        "energy_change": values[2],  # dE
                        "electronic_steps": electronic_steps,
                    }
                # check if we have a molecular dynamics calculation
                elif len(values) in [7, 8]:
                    ionic_step = {
                        "temperature": values[0],  # T
                        "energy_gibbs": values[1],  # E (total energy, kinetic, nose)
                        "energy": values[2],  # F (total_free_energy)
                        "energy_sigma_zero": values[3],  # E0
                        "energy_kinetic": values[4],  # EK
                        "energy_potential_nose_thermostat": values[5],  # SP
                        "energy_kinetic_nose_thermostat": values[6],  # SK
                        "electronic_steps": electronic_steps,
                    }

                # otherwise something went wrong
                else:
                    raise Exception(
                        "Electronic step had unexpected data. Failed to parse."
                    )

                # If the length of the values list is 4 or 8, then that means
                # we also have a "mag" value attatched at the end of our values
                if len(values) in [4, 8]:
                    ionic_step.update({"magnetic": values[-1]})

                # for the very first electronic step, VASP provides an energy-change
                # value, which they set equal to the energy itself. This is misleading
                # in analysis so we remove it.
                # As an example of why this is important, this will cause problems
                # in the PotimErrorHandler when the original structure is a poor
                # guess and positive energy. The handler will mistakenly think
                # the energy changes are getting worse -- which is not the case
                # because we only look at the first step!
                if not self.ionic_steps:
                    ionic_step["energy_change"] = numpy.NaN
                # take whatever ionic_step that was made above and add it to our
                # results list!
                self.ionic_steps.append(ionic_step)
            # Otherwise this line is an electronic step
            else:

                # electronic step lines are pretty easy because they are just
                # a row in a table of electronic steps. First let's split
                # the values into and list and then convert them into floats.
                # Note we remove the first two values because these are the
                # scheme used (i.e. DAV, RMM, or CG) and electronic step number
                # which we don't need. (I grab the scheme below though)
                # BUG: sometimes VASP prints a value like '-0.33328-312' which
                # can't be converted to a float. I need a try/except here to
                # catch this case and return a numpy.NAN instead.
                def try_float(value):
                    try:
                        return float(value)
                    except:
                        return numpy.NaN

                values = [try_float(value) for value in line.split()[2:]]

                # now load the data into a dictionary for verbosity
                # Note that I change the VASP headers to more verbose names so
                # the user can instantly see their meaning. The original headers
                # are shown as comments next to each.
                electronic_step = {
                    # The scheme is set by IALGO and is the first thing written
                    # in the line. Rather than grab it above, I just do it here.
                    "scheme": line.split()[0].replace(":", ""),
                    "energy": values[0],  # E
                    "energy_change": values[1],  # dE
                    "band_structure_energy_change": values[2],  # d eps
                    "nhamiltonians": values[3],  # ncg
                    "wavefunctions_residuum_norm": values[4],  # rms
                    # Note not all electronic steps have this value so we need to doublecheck
                    "charge_density_change": values[5]
                    if len(values) == 6
                    else None,  # rms(c)
                }

                # add the electronic step to our results!
                electronic_steps.append(electronic_step)

                # SPECIAL CASE:
                # if this is the final line and isn't an ionic step summary,
                # then that means we are in the middle of the ionic step and
                # are reading an incomplete file. We still want all the
                # electronic steps available in the final class so we store
                # the incomplete ionic step here. This is useful for ErrorHandlers.
                # We use numpy.NaN instead of None so errors aren't through
                # elsewhere that expect a float value.
                if line_number == len(lines) - 1:
                    # BUG: we don't know what the data should be here (see the
                    # three formats discussed above). For now, we assume
                    # the first format as it is most common. We are filling this
                    # data with "None" values anyways so it shouldn't matter.
                    ionic_step = {
                        "energy": numpy.NaN,  # F (total_free_energy)
                        "energy_sigma_zero": numpy.NaN,  # E0
                        "energy_change": numpy.NaN,  # dE
                        "electronic_steps": electronic_steps,
                    }
                    self.ionic_steps.append(ionic_step)

    def all_electronic_step_energies(self, ionic_step_number):
        # TODO: move to DftCalc/IonicStep/ElectronicStep class
        pass

    def all_ionic_step_energies(self):
        # TODO: move to DftCalc/IonicStep/ElectronicStep class
        pass

    @property
    def energy_final(self):
        # TODO: move to DftCalc/IonicStep/ElectronicStep class
        return self.ionic_steps[-1]["energy_sigma_zero"]
