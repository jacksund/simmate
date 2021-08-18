# -*- coding: utf-8 -*-

# !!! In the future, I think this should be a "converter" class that loads data
# into a more generic DftResults class -- so one that is more generically for
# storing electronic and ionic steps across different calculators. I think it
# would be useful to have a ElectronicStep and IonicStep classes.

# BUG: what if the final ionic_step hasn't completed yet? I need to account for this.
# Maybe I could have the ionic step with None values and fill in the electronic steps
# where they're available.


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

        # now let's iterate through the contents and parse the data
        for line in lines:

            # if "N" is in the line, that means we have the start of a new ionic step
            if "N" in line:

                # let's start with an empty list to record all of the electronic
                # steps. Note this will also reset the list every time we start
                # a new ionic step.
                electronic_steps = []

            # if "F" is in the line, that means we have hit the end of an ionic step
            elif "F" in line:

                # parse this line to pull out the ionic_step information
                # The formatting is whacky, so I decided to remove all variable
                # names, leaving only a list of values. I then split these values
                # into a list that I can more easily work with.
                values = (
                    line.strip()
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
                # value which is just the ionic_step_number and we don't need
                values = [float(value) for value in values[1:]]

                # Now there are three formats that we need to account for, which
                # each have a different amount of information given, and we can
                # figure out the type easy based on the length of our list of
                # values. These are...
                #   (1) non-magnetic calculations (F, E0, dE)
                #   (2) magnetic calculations (F, E0, dE, mag)
                #   (3) molecular dynamics calculations (T, E, F, E0, EK, SP, SK)

                # check if we have a non-magnetic calculation
                if len(values) == 3:
                    ionic_step = {
                        "energy": values[0],  # F (total_free_energy)
                        "energy_sigma_zero": values[1],  # E0
                        "energy_change": values[2],  # dE
                        "electronic_steps": electronic_steps,
                    }

                # check if we have a magnetic calculation
                elif len(values) == 4:
                    ionic_step = {
                        "energy": values[0],  # F (total_free_energy)
                        "energy_sigma_zero": values[1],  # E0
                        "energy_change": values[2],  # dE
                        "magnetic": values[3],  # mag
                        "electronic_steps": electronic_steps,
                    }

                # check if we have a molecular dynamics calculation
                elif len(values) == 7:
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
                values = [float(value) for value in line.split()[2:]]

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

    def all_electronic_step_energies(self, ionic_step_number):
        # TODO: move to DftCalc/IonicStep/ElectronicStep class
        pass

    def all_ionic_step_energies(self):
        # TODO: move to DftCalc/IonicStep/ElectronicStep class
        pass

    @property
    def final_energy(self):
        # TODO: move to DftCalc/IonicStep/ElectronicStep class
        return self.ionic_steps[-1]["energy_sigma_zero"]
