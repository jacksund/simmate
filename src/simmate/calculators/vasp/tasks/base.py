# -*- coding: utf-8 -*-

import os

# TODO: write my own vasp.outputs classes and remove pymatgen dependency
from pymatgen.io.vasp.outputs import Vasprun

from simmate.calculators.vasp.inputs.all import Incar, Poscar, Kpoints, Potcar
from simmate.workflows.core.tasks.supervisedstagedtask import (
    SupervisedStagedShellTask as SSSTask,
)


class VaspTask(SSSTask):

    # Vasp calculations always need an input structure
    requires_structure = True

    # The command to call vasp in the current directory
    # TODO: add support for grabbing a user-set default from their configuration
    command = "vasp > vasp.out"

    # set the default vasp settings from a dictionary. This is the one thing
    # you *must* set when subclassing VaspTask. An example is:
    #   incar = dict(NSW=0, PREC="Accurate", KSPACING=0.5)
    incar = None
    # TODO: add options for poscar formation
    # add_selective_dynamics=False
    # add_velocities=False
    # significant_figures=6

    # set the KptGrid or KptPath object
    # TODO - KptGrid is just a float for now
    # NOTE - this is optional because you can have KSPACING as an INCAR argument.
    # If KSPACING is set above, we ignore whatever is set here.
    kpoints = None

    # This directs which Potcar files to grab. You would set this to a string
    # of what you want, such as "PBE", "PBE_GW", or "LDA"
    functional = None

    # This is an optional parameter to override Simmate's default selection of
    # potentials based off of the functional chosen. The defaults are located
    # in simmate.calculators.vasp.inputs.potcar_mappings. You can supply your
    # own mapping dictionary or you can take ours and update the specific
    # potentials you'd like. For example:
    #   from simmate.calculators.vasp.inputs.potcar_mappings import PBE_ELEMENT_MAPPINGS
    #   element_mappings = PBE_ELEMENT_MAPPINGS.copy().update({"C": "C_h"})
    # or if you only use Carbon and don't care about other elements...
    #   element_mappings = {"C": "C_h"}
    # Read more on this inside the Potcar class and be careful with updating!
    potcar_mappings = None

    def __init__(
        self,
        incar=None,
        kpoints=None,
        functional=None,
        potcar_mappings=None,
        # To support other options from the Simmate SSSTask and Prefect Task
        **kwargs,
    ):

        # if any of these input parameters were given, overwrite the default
        # Note to python devs: this odd formatting is because we set our defaults
        # to None in __init__ while our actual default values are define above
        # as class attributes. This may seem funky at first glance, but it
        # makes inheriting from this class extremely pretty!
        # This code is effectively the same as @defaults_from_attrs(...)
        if incar:
            self.incar = incar
        if kpoints:
            self.kpoints = kpoints
        if functional:
            self.functional = functional
        if potcar_mappings:
            self.potcar_mappings = potcar_mappings

        # now inherit from parent SSSTask class
        super().__init__(**kwargs)

    def setup(self, structure, directory):

        # TODO should I sanitize the structure first? primitive and LLL reduce?

        # write the poscar file
        Poscar.to_file(structure, os.path.join(directory, "POSCAR"))

        # write the incar file
        Incar(**self.incar).to_file(structure, os.path.join(directory, "INCAR"))

        # if KSPACING is not provide in the incar AND kpoints is attached to this
        # class instance, then we write the KPOINTS file
        if self.kpoints and ("KSPACING" not in self.incar):
            Kpoints.to_file(
                structure,
                self.kpoints,
                os.path.join(directory, "KPOINTS"),
            )

        # write the POTCAR file
        Potcar.to_file_from_type(
            structure.composition.elements,
            self.functional,
            os.path.join(directory, "POTCAR"),
            self.potcar_mappings,
        )

    def workup(self, directory):
        """
        This is the most basic VASP workup where I simply load the final structure,
        final energy, and confirm convergence. I will likely make this a common
        function for this vasp module down the road.
        """

        # load the xml file and only parse the bare minimum
        xmlReader = Vasprun(
            filename=os.path.join(directory, "vasprun.xml"),
            parse_dos=False,
            parse_eigen=False,
            parse_projected_eigen=False,
            parse_potcar_file=False,
            exception_on_bad_xml=True,
        )

        # grab the final structure
        final_structure = xmlReader.structures[-1]

        # grab the energy per atom
        final_energy = xmlReader.final_energy / final_structure.num_sites

        # confirm that the calculation converged
        assert xmlReader.converged

        # return the desired info
        # TODO: in the future, I may just want to return the VaspRun object
        # by default.
        return final_structure, final_energy
