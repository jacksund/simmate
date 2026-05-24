# -*- coding: utf-8 -*-

from simmate.apps.quantum_espresso.outputs import PwscfXml
from simmate.apps.vasp.outputs import Vasprun

from ..core import table_column
from .calculation import Calculation
from .forces import Forces
from .structure import Structure
from .thermodynamics import Thermodynamics

# OPTIMIZE: consider lazy loading PwscfXml and Vasprun bc these apps are optional


class StaticEnergy(Structure, Thermodynamics, Forces, Calculation):

    class Meta:
        app_label = "workflow_explorer"
        db_table = "workflows_staticenergy"


    # -------------------------------------------------------------------------

    @classmethod
    def from_vasp_run(cls, vasprun: Vasprun, as_dict: bool = False):
        # Takes a pymatgen VaspRun object, which is what's typically returned
        # from a simmate VaspWorkflow.run() call.

        # The data is actually easier to access as a dictionary and everything
        # we need is stored under the "output" key.
        data = vasprun.as_dict()["output"]
        # In a static energy calculation, there is only one ionic step so we
        # grab that up front.
        ionic_step = data["ionic_steps"][0]

        # Take our structure, energy, and forces to build all of our other
        # fields for this datatable
        static_energy = cls.from_toolkit(
            structure=vasprun.final_structure,
            energy=ionic_step["e_wo_entrp"],
            site_forces=ionic_step["forces"],
            lattice_stress=ionic_step["stress"],
            as_dict=as_dict,
        )

        # If we don't want the data as a dictionary, then we are saving a new
        # object and can go ahead and do that here.
        if not as_dict:
            static_energy.save()

        return static_energy

    @classmethod
    def from_pwscf_run(cls, pwscf_run: PwscfXml, as_dict: bool = False):
        # Take our structure, energy, and forces to build all of our other
        # fields for this datatable
        static_energy = cls.from_toolkit(
            structure=pwscf_run.final_structure,
            energy=pwscf_run.final_energy,
            # DISABLED FOR TESTING:
            site_forces=pwscf_run.final_site_forces.tolist(),
            lattice_stress=pwscf_run.final_lattice_stress.tolist(),
            as_dict=as_dict,
        )

        # If we don't want the data as a dictionary, then we are saving a new
        # object and can go ahead and do that here.
        if not as_dict:
            static_energy.save()

        return static_energy
