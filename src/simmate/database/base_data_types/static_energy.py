# -*- coding: utf-8 -*-

from simmate.apps.quantum_espresso.outputs import PwscfXml
from simmate.apps.vasp.outputs import Vasprun
from simmate.database.base_data_types import (
    Calculation,
    Forces,
    Structure,
    Thermodynamics,
    table_column,
)

# OPTIMIZE: consider lazy loading PwscfXml and Vasprun bc these apps are optional


class StaticEnergy(Structure, Thermodynamics, Forces, Calculation):
    class Meta:
        app_label = "workflows"

    archive_fields = [
        "valence_band_maximum",
        "conduction_band_minimum",
        "energy_fermi",
        "is_gap_direct",
    ]

    api_filters = dict(
        band_gap=["range"],
        is_gap_direct=["exact"],
        energy_fermi=["range"],
        conduction_band_minimum=["range"],
        valence_band_maximum=["range"],
    )

    # OPTIMIZE: should I include this electronic data?

    band_gap = table_column.FloatField(blank=True, null=True)
    """
    The band gap energy in eV.
    """

    is_gap_direct = table_column.BooleanField(blank=True, null=True)
    """
    Whether the band gap is direct or indirect.
    """

    energy_fermi = table_column.FloatField(blank=True, null=True)
    """
    The Fermi energy in eV.
    """

    conduction_band_minimum = table_column.FloatField(blank=True, null=True)
    """
    The conduction band minimum in eV.
    """

    valence_band_maximum = table_column.FloatField(blank=True, null=True)
    """
    The valence band maximum in eV.
    """

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
            band_gap=data.get("bandgap"),
            is_gap_direct=data.get("is_gap_direct"),
            energy_fermi=data.get("efermi"),
            conduction_band_minimum=data.get("cbm"),
            valence_band_maximum=data.get("vbm"),
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
            site_forces=pwscf_run.site_forces.tolist(),
            lattice_stress=pwscf_run.lattice_stress.tolist(),
            # TODO: I have not parsed this info out yet
            # band_gap=None,
            # is_gap_direct=None,
            # energy_fermi=None,
            # conduction_band_minimum=None,
            # valence_band_maximum=None,
            as_dict=as_dict,
        )

        # If we don't want the data as a dictionary, then we are saving a new
        # object and can go ahead and do that here.
        if not as_dict:
            static_energy.save()

        return static_energy
