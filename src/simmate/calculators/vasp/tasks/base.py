# -*- coding: utf-8 -*-

import os

from prefect.utilities.tasks import defaults_from_attrs
from pymatgen.io.vasp.outputs import Vasprun

from simmate.calculators.vasp.inputs import Incar, Poscar, Kpoints, Potcar
from simmate.utilities import get_directory
from simmate.workflows.core.tasks.stagedshelltask import (
    StagedShellTask,
    StructureRequiredError,
)


class VaspTask(StagedShellTask):

    # The command to call vasp in the current directory
    # TODO: add support for grabbing a user-set default from their configuration
    command = "vasp > vasp.out"

    # Vasp calculations always need an input structure
    requires_structure = True

    # set the default vasp settings from a dictionary. This is the one thing
    # you *must* set when subclassing VaspTask. An example is:
    #   incar = dict(NSW=0, PREC="Accurate", KSPACING=0.5)
    incar = None

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
    #   from simmate.calculators.vasp.inputs.potcar_mappings import ELEMENT_MAPPINGS
    #   potcar_mappings = ELEMENT_MAPPINGS[functional].update({"C": "C_h"})
    # Read more on this inside the Potcar class and be careful with updating!
    potcar_mappings = None

    def __init__(
        self,
        # optional setup parameters
        command=None,
        dir=None,
        # these are the inputs for
        structure=None,
        incar=None,
        kpoints=None,
        functional=None,
        potcar_mappings=None,
        # To support other Prefect input options
        **kwargs,
    ):

        # if any of these input parameters was given, overwrite the default
        # Note to python devs: this odd formatting is because we set our defaults
        # to None in __init__ while our actualt default values are define above
        # as class attributes. This may seem funky at first glance, but it
        # makes inheriting from this class extremely pretty :)
        if command:
            self.command = command
        if structure:
            self.structure = structure
        if incar:
            self.incar = incar
        if kpoints:
            self.kpoints = kpoints
        if functional:
            self.functional = functional
        if potcar_mappings:
            self.potcar_mappings = potcar_mappings

        # These parameters will never have a default, so go ahead and set them
        # establish the working directory for this Task
        self.dir = dir
        self.structure = structure

        # now inherit the parent Prefect Task class
        super().__init__(**kwargs)

    @defaults_from_attrs(
        "dir", "structure", "incar", "kpoints", "functional", "potcar_mappings"
    )
    def setup(
        self,
        dir=None,
        structure=None,
        incar=None,
        kpoints=None,
        functional=None,
        potcar_mappings=None,
    ):

        # TODO should I sanitize the structure first? primitive and LLL reduce?

        # write the poscar file
        Poscar.write_file(structure, os.path.join(dir, "POSCAR"))

        # write the incar file
        Incar(**incar).write_file(os.path.join(dir, "INCAR"))

        # if KSPACING is not provided AND kpoints is, write the KPOINTS file
        if kpoints and ("KSPACING" not in incar):
            Kpoints.write_file(
                structure,
                kpoints,
                os.path.join(dir, "KPOINTS"),
            )

        # write the POTCAR file
        Potcar(
            structure.species,
            functional,
            os.path.join(dir, "POTCAR"),
            potcar_mappings,
        )

    @defaults_from_attrs("dir")
    def postprocess(self, dir=None):
        """
        This is the most basic VASP workup where I simply load the final structure,
        final energy, and confirm convergence. I will likely make this a common
        function for this vasp module down the road.
        """

        # load the xml file and only parse the bare minimum
        xmlReader = Vasprun(
            filename=os.path.join(dir, "vasprun.xml"),
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

    @defaults_from_attrs(
        "command",
        "dir",
        "structure",
        "incar",
        "kpoints",
        "functional",
        "potcar_mappings",
    )
    def run(
        self,
        command=None,
        dir=None,
        structure=None,
        incar=None,
        kpoints=None,
        functional=None,
        potcar_mappings=None,
    ):
        """
        Runs the entire job in the current working directory without any error
        handling. If you want robust error handling, then you should instead
        run this through the SupervisedJobTask class. This method should
        very rarely be used!
        """
        if not structure and self.requires_structure:
            raise StructureRequiredError("a structure is required as an input")
        dir = get_directory(dir)
        self.setup(dir, structure, incar, kpoints, functional, potcar_mappings)
        self.execute(command, dir, wait_until_complete=True)
        result = self.postprocess(dir)
        return result
