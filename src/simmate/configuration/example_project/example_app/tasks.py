# -*- coding: utf-8 -*-

"""
This file is for any custom Tasks you may need in your workflows. For example,
you may want to write a new VaspTask that has custom INCAR settings. These tasks
can be incorporated into our workflows (in `workflows.py`).

Below is an example of a simple VaspTask, which is used to run a single VASP
calculation.

For more information and advanced guides, be sure to read through our
[S3Task documentation](https://jacksund.github.io/simmate/simmate/workflow_engine/supervised_staged_shell_task.html)
as well as relevent subclasses like the
[VaspTask documentation](https://jacksund.github.io/simmate/simmate/calculators/vasp/tasks/base.html)
"""


from simmate.calculators.vasp.inputs import Incar
from simmate.calculators.vasp.tasks.base import VaspTask
from simmate.calculators.vasp.inputs.potcar_mappings import (
    PBE_ELEMENT_MAPPINGS_LOW_QUALITY,
)
from simmate.calculators.vasp.error_handlers import (
    Unconverged,
    NonConverging,
    Frozen,
    Walltime,
    # There are many more available too!
)


class ExampleRelaxation(VaspTask):

    # This uses the PBE functional with POTCARs that have lower electron counts
    # and convergence criteria when available.
    functional = "PBE"
    potcar_mappings = PBE_ELEMENT_MAPPINGS_LOW_QUALITY

    # These are all input settings for this task.
    incar = dict(
        # These settings are the same for all structures regardless of composition.
        PREC="Normal",
        EDIFF=1e-5,
        ENCUT=450,  # !!! Should this be based on the element type?
        ISIF=3,
        NSW=100,
        IBRION=1,
        POTIM=0.02,
        LCHARG=False,
        LWAVE=False,
        KSPACING=0.4,
        # The type of smearing we use depends on if we have a metal, semiconductor,
        # or insulator. So we need to decide this using a keyword modifier.
        multiple_keywords__smart_ismear={
            "metal": dict(
                ISMEAR=1,
                SIGMA=0.06,
            ),
            "non-metal": dict(
                ISMEAR=0,
                SIGMA=0.05,
            ),
        },
        # This is a dummy example of using custom modifiers. This would set the
        # incar value of EXAMPLE=16 for structure with 2 sites (2*8=16). Note,
        # we registered "multiply_nsites" logic below.
        EXAMPLE__multiply_nsites=8,
    )

    # These are some default error handlers to use. Note the order matters here!
    # Only the first error handler triggered in this list will be used before
    # restarting the job
    error_handlers = [
        Unconverged(),
        NonConverging(),
        Frozen(),
        Walltime(),
    ]


# If you need to add advanced logic for one of your INCAR tags, you can register
# a keyword_modifier to the INCAR class like so:

# first define the logic of your modifier as a function
def keyword_modifier_multiply_nsites(structure, example_mod_input):
    # add your advanced logic to determine the keyword value.
    return structure.num_sites * example_mod_input


# then register modifier with the Incar class
Incar.add_keyword_modifier(keyword_modifier_multiply_nsites)
