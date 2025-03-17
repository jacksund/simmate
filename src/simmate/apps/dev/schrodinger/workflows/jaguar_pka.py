# -*- coding: utf-8 -*-

from pathlib import Path

from simmate.apps.dev.schrodinger.inputs import JaguarInput
from simmate.workflows.base_flow_types import S3Workflow
from simmate.toolkit import Molecule


class Pka__Schrodinger__JaguarPka(S3Workflow):
    """
    Calculates micro-pKa of a molecule using Schrodinger's Jaguar pKa pipeline.
    By default, we use `ipkasearch=all` which means we let Jaguar automatically
    determine potential basic atoms or acidic hydrogens.

    On a single CPU core, a single small molecule will take 30min-2hrs.

    The pKa's calculated have a RMSE of 0.63 compared to experimental values,
    and the errors appear to be normally distributed. This means ~95% of
    predicted pKa's are within +/-1.26 of the experimental value. See background
    info below for more info.

    Helpful links:
     - [Background on Schrodinger pKa calcs](https://www.schrodinger.com/wp-content/uploads/2023/10/Schrodinger-solutions-for-small-molecule-protonation-state-enumeration-and-pKa-prediction.pdf)
     - [Jaguar pKa Examples](https://learn.schrodinger.com/private/edu/release/current/Documentation/html/jaguar/jaguar_command_reference/jaguar_input_setup_pka.htm)
     - [Jaguar pKa Settings](https://learn.schrodinger.com/private/edu/release/current/Documentation/html/jaguar/jaguar_command_reference/jaguar_input_gen_pka.htm)
    """

    use_database = False

    command = "jaguar run pka.py settings.in > jaguar.out"
    required_files = ["settings.in"]

    # TODO: LSF sometimes doesn't end job even when it is finished
    monitor = False
    # monitor_freq = 30
    # error_handlers = [HangingJaguarJob]

    gen: dict = dict(
        ipka_prot_deprot="both",
        ipkasearch="all",
        ipka_solv_opt=1,
        ipka_max_conf=10,
        ipka_csrch_acc=1,
    )
    """
    key-value pairs for the `&gen` section of `settings.in`
    """

    @classmethod
    def setup(
        cls,
        molecule: Molecule,
        directory: Path,
        convert_to_3d: bool = False,
        **kwargs,
    ):
        settings = JaguarInput(
            molecule=molecule,
            gen=cls.gen,
            convert_to_3d=convert_to_3d,
        )
        settings.to_file(directory / "settings.in")

    # @staticmethod
    # def workup(directory):
    #     # TODO
    #     return
