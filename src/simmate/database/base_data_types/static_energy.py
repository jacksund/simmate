# -*- coding: utf-8 -*-

from simmate.database.base_data_types import (
    table_column,
    Structure,
    Forces,
    Thermodynamics,
    Calculation,
)


class StaticEnergy(Structure, Thermodynamics, Forces, Calculation):
    class Meta:
        abstract = True
        app_label = "local_calculations"

    base_info = (
        [
            "valence_band_maximum",
            "conduction_band_minimum",
            "energy_fermi",
            "is_gap_direct",
        ]
        + Structure.base_info
        + Thermodynamics.base_info
        + Forces.base_info
        + Calculation.base_info
    )

    # Note: we assume that only converged data is being stored! So there is no
    # "converged_electronic" section here. ErrorHandlers and workups should
    # ensure this.

    # This data here is something we only get for the final structure, so it
    # may make sense to move this data into the IonicStepStructure table (and
    # allow null values for non-final steps). I instead keep this here because
    # I don't want columns above that are largely empty.
    # Note: all entries are optional because there is no guaruntee the calculation
    # finishes successfully
    band_gap = table_column.FloatField(blank=True, null=True)
    is_gap_direct = table_column.BooleanField(blank=True, null=True)
    energy_fermi = table_column.FloatField(blank=True, null=True)
    conduction_band_minimum = table_column.FloatField(blank=True, null=True)
    valence_band_maximum = table_column.FloatField(blank=True, null=True)

    def update_from_vasp_run(self, vasprun, corrections, directory):
        # Takes a pymatgen VaspRun object, which is what's typically returned
        # from a simmate VaspTask.run() call.

        # The data is actually easier to access as a dictionary and everything
        # we need is stored under the "output" key.
        data = vasprun.as_dict()["output"]
        # In a static energy calculation, there is only one ionic step so we
        # grab that up front.
        ionic_step = data["ionic_steps"][0]

        # Take our structure, energy, and forces to build all of our other
        # fields for this datatable
        # OPTIMIZE: this overwrites structure data, which should already be there.
        # Is there a faster way to grab this data and update attributes?
        new_kwargs = self.from_toolkit(
            structure=vasprun.final_structure,
            energy=ionic_step["e_wo_entrp"],
            site_forces=ionic_step["forces"],
            lattice_stress=ionic_step["stress"],
            as_dict=True,
        )
        for key, value in new_kwargs.items():
            setattr(self, key, value)

        # There is also extra data for the final structure that we save directly
        # in the relaxation table. We use .get() in case the key isn't provided
        self.band_gap = data.get("bandgap")
        self.is_gap_direct = data.get("is_gap_direct")
        self.energy_fermi = data.get("efermi")
        self.conduction_band_minimum = data.get("cbm")
        self.valence_band_maximum = data.get("vbm")

        # lastly, we also want to save the corrections made and directory it ran in
        self.corrections = corrections
        self.directory = directory

        # Now we have the relaxation data all loaded and can save it to the database
        self.save()
