# -*- coding: utf-8 -*-

import os

# TODO: write my own vasp.outputs classes and remove pymatgen dependency
from pymatgen.io.vasp.inputs import Kpoints
from pymatgen.analysis.structure_matcher import StructureMatcher
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
from pymatgen.symmetry.bandstructure import HighSymmKpath

from simmate.calculators.vasp.inputs.all import Incar, Poscar, Potcar
from simmate.calculators.vasp.tasks.base import VaspTask

# TODO: This class only exists because I don't have the core KptPath class
# written yet. Because my labmates have a high priority on BandStructure
# calculations, I needed to make this temporary workaround class.


class BandStructureTask(VaspTask):

    # The default settings to use for this calculation.
    # The key thing for band structures is that this follows a static energy
    # calculation. We use the CHGCAR from that previous calculation. We also
    # hold the charge density static during this calculation so this is a
    # non-selfconsistent (non-SCF) calculation.
    incar = dict(
        EDIFF=1.0e-07,
        ENCUT=520,
        ICHARG=11,  # this indicates we are using a previous CHGCAR
        ISMEAR=0,
        LCHARG=False,
        LWAVE=False,
        NSW=0,
        PREC="Accurate",
        SIGMA=0.05,
    )

    # We will use the PBE functional with all default mappings
    functional = "PBE"

    # set the KptGrid or KptPath object
    # TODO: in the future, all functionality of this class will be available
    # by giving this class a KptPath class here.
    kpoints = None
    kpoints_line_density = 20

    def setup(self, structure, dir):

        # For band structures, we need to make sure the structure is in the
        # standardized primitive form. Note we assume that we are using the
        # "interanational_monoclinc" in pymatgen.
        # We use the same SYMPREC from the INCAR, which is 1e-5 if not set.
        sym_prec = self.incar.get("SYMPREC", 1e-5) if self.incar else 1e-5
        sym_finder = SpacegroupAnalyzer(structure, symprec=sym_prec)
        structure_standardized = sym_finder.get_primitive_standard_structure()
        # check for pymatgen bugs here
        check_for_standardization_bugs(structure, structure_standardized)

        # write the poscar file
        Poscar.to_file(structure_standardized, os.path.join(dir, "POSCAR"))

        # write the incar file
        Incar(**self.incar).to_file(os.path.join(dir, "INCAR"))

        ##############
        # Now we need to find the high-symmetry Kpt path. Note that all of this
        # functionality will be moved to the KptPath class and then extended to
        # vasp.inputs.kpoints class. Until those classes are ready, we just use
        # pymatgen here.
        kpath = HighSymmKpath(structure)
        frac_k_points, k_points_labels = kpath.get_kpoints(
            line_density=self.kpoints_line_density,
            coords_are_cartesian=False,
        )
        kpoints = Kpoints(
            comment="Non SCF run along symmetry lines",
            style=Kpoints.supported_modes.Reciprocal,
            num_kpts=len(frac_k_points),
            kpts=frac_k_points,
            labels=k_points_labels,
            kpts_weights=[1] * len(frac_k_points),
        )
        kpoints.write_file(os.path.join(dir, "KPOINTS"))
        ##############

        # write the POTCAR file
        Potcar.to_file_from_type(
            structure.composition.elements,
            self.functional,
            os.path.join(dir, "POTCAR"),
            self.potcar_mappings,
        )


def check_for_standardization_bugs(structure_original, structure_new):

    # In pymatgen, they include this code with the standardization of their
    # structures because there were several bugs in the past and they want to
    # double-check themselves. I'm still using their code to standardize
    # my structures, so I should make this check too.

    vpa_old = structure_original.volume / structure_original.num_sites
    vpa_new = structure_new.volume / structure_new.num_sites

    if abs(vpa_old - vpa_new) / vpa_old > 0.02:
        raise ValueError(
            f"Standardizing cell failed! Volume-per-atom changed... old: {vpa_old}, new: {vpa_new}"
        )

    sm = StructureMatcher()
    if not sm.fit(structure_original, structure_new):
        raise ValueError("Standardizing cell failed! Old structure doesn't match new.")
