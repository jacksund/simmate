# -*- coding: utf-8 -*-

from simmate.engine import S3Workflow


# TODO: add StructureInputWorkflow mixin which can be made from VaspWorkflow class
class PwscfWorkflow(S3Workflow):
    required_files = ["settings.in"]

    command: str = "pw.x < settings.in > pw-scf.out"
    """
    The command to call PW-SCF, which is typically `pw.x`.
    """

    # -------------------------------------------------------------------------

    # We set each section of PW-SCF's input parameters as a class attribute
    # https://www.quantum-espresso.org/Doc/INPUT_PW.html

    control: dict = None
    """
    key-value pairs for the `&CONTROL` section of `settings.in`
    """

    system: dict = None
    """
    key-value pairs for the `&SYSTEM` section of `settings.in`
    """

    electrons: dict = None
    """
    key-value pairs for the `&ELECTRONS` section of `settings.in`
    """

    ions: dict = None
    """
    key-value pairs for the `&IONS` section of `settings.in`
    """

    fcp: dict = None
    """
    key-value pairs for the `&FCP` section of `settings.in`
    """

    rism: dict = None
    """
    key-value pairs for the `&RISM` section of `settings.in`
    """

    @classmethod
    @property
    def full_settings(cls) -> dict:
        # TODO: consider making this use PwscfInput class
        return dict(
            control=cls.control,
            system=cls.system,
            electrons=cls.electrons,
            ions=cls.ions,
            fcp=cls.fcp,
            rism=cls.rism,
        )

    # -------------------------------------------------------------------------
