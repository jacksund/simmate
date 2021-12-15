# -*- coding: utf-8 -*-

# THIS FILE IS INCOMPLETE
# This is just an outline

from simmate.calculators.vasp.tasks.base import VaspTask
from simmate.calculators.vasp.tasks.relaxation.third_party.mit import MITRelaxationTask

# https://www.vasp.at/wiki/index.php/XANES_in_Diamond


class InitialStateApprox(VaspTask):

    # Take the incar from MIT relaxation and update a few of its inputs.
    # Note we use "copy" to prevent the original settings from changing
    incar = MITRelaxationTask.incar.copy()
    incar.update(
        dict(
            # change to a static energy
            NSW=0,
            IBRION=-1,
            # and turn on the initial state approx
            ICORELEVEL=1,
            LVTOT=True,
        ),
    )

    def setup():

        # slab pymatgen SlabGenerator
        # Create a slab of the lowest-energy-surface (e.g. 001 for our layered electrides)
        # and test for convergence based on slab thickness. Lauren tests 6-12 layers
        # and observed convergence at roughly 10 layers for Sc2C.

        pass

    def workup():

        # empirically correct against experimental data

        pass
