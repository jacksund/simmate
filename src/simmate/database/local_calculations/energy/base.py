# -*- coding: utf-8 -*-

from simmate.database.base_data_types import (
    table_column,
    Structure,
    Forces,
    Thermodynamics,
    Calculation,
)

# WARNING:
# The from_pymatgen and update_from_vasp_run methods don't work yet!


class StaticEnergy(Structure, Thermodynamics, Forces, Calculation):

    """Base Info"""

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

    """ Model Methods """

    @classmethod
    def from_pymatgen(
        cls,
        structure,
        energy,
        site_forces,
        lattice_stress,
        as_dict=False,
    ):
        # because this is a combination of tables, I need to build the data for
        # each and then feed all the results into this class

        # first grab the full dictionaries for each parent model
        thermo_data = Thermodynamics.from_base_data(
            structure,
            energy,
            as_dict=True,
        )
        forces_data = Forces.from_base_data(
            structure,
            site_forces,
            lattice_stress,
            as_dict=True,
        )
        structure_data = Structure.from_pymatgen(structure, as_dict=True)

        # Now feed all of this dictionarying into one larger one.
        all_data = dict(
            **structure_data,
            **thermo_data,
            **forces_data,
        )

        # If as_dict is false, we build this into an Object. Otherwise, just
        # return the dictionary
        return all_data if as_dict else cls(**all_data)

    def update_from_vasp_run(self, vasprun, corrections, IonicStepStructure_subclass):
        # Takes a pymatgen VaspRun object, which is what's typically returned
        # from a simmate VaspTask.run() call.
        # The ionic_step_structure_subclass is where to save the structures and
        # is a subclass of IonicStepStructure.

        # The data is actually easier to access as a dictionary and everything
        # we need is stored under the "output" key
        data = vasprun.as_dict()["output"]

        # The only other data we need to grab is the list of structures. We can
        # pull the structure for each ionic step from the vasprun class directly.
        structures = vasprun.structures

        # Now let's iterate through the ionic steps and save these to the database.
        for number, (structure, ionic_step) in enumerate(
            zip(structures, data["ionic_steps"])
        ):
            # first pull all the data together and save it to the database
            structure = IonicStepStructure_subclass.from_pymatgen(
                number,
                structure,
                energy=ionic_step["e_wo_entrp"],
                site_forces=ionic_step["forces"],
                lattice_stress=ionic_step["stress"],
                relaxation=self,  # this links the structure to this relaxation
            )
            structure.save()

            # If this is the first structure, we want to link it as such
            if number == 0:
                self.structure_start_id = structure.id
            # and same for the final structure
            elif number == len(structures) - 1:
                self.structure_final_id = structure.id
        # calculate extra data for storing
        self.volume_change = (
            structures[-1].volume - structures[0].volume
        ) / structures[0].volume

        # There is also extra data for the final structure that we save directly
        # in the relaxation table
        self.band_gap = data["bandgap"]
        self.is_gap_direct = data["is_gap_direct"]
        self.energy_fermi = data["efermi"]
        self.conduction_band_minimum = data["cbm"]
        self.valence_band_maximum = data["vbm"]

        # lastly, we also want to save the corrections made
        self.corrections = corrections

        # Now we have the relaxation data all loaded and can save it to the database
        self.save()

    """ Set as Abstract Model """
    # I have other models inherit from this one, while this model doesn't need
    # its own table.
    class Meta:
        abstract = True
        app_label = "local_calculations"
