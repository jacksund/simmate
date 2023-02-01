# -*- coding: utf-8 -*-

from pymatgen.symmetry.analyzer import SpacegroupAnalyzer

from simmate.toolkit import Structure
from simmate.toolkit.transformations.base import Transformation


class ExtremeSymmetry(Transformation):
    """
    Applies a series of increasingly excessive symmetry checks -- starting
    at 0.1 Angstrom + 0.5 Deg and ending at ~3 Angstrom + ~40 Deg. The final
    tolerance checks are massive tolerances that are intended to reduce the
    structure to a new and distinct one.

    This will return the highly symmetrized structure, which is often useful
    for evolutionary searches where many disordered structures exist. We expect
    it to be most effective for structures with high site counts.
    """

    ninput = 1
    io_scale = "one_to_one"
    allow_parallel = True

    @staticmethod
    def apply_transformation(structure: Structure):
        # To establish the original structure symmetry, we begin with strict
        # tolerances of 0.01Angstrom and 0.5 Deg cutoffs
        sga = SpacegroupAnalyzer(
            structure,
            symprec=0.01,
            angle_tolerance=0.5,
        )
        original_spacegroup = sga.get_space_group_number()

        # As we try higher tolerances, we want to keep track of when we find
        # a new & higher spacegroup.
        results = {original_spacegroup: [0.01, 0.5]}
        symprec = 0.1
        angle_tol = 0.5

        # This cycle attempts symmetry reduction at different tolerances.
        # The tolerances increase as we go, and no matter what, 24 different
        # attempts will be made.
        for attempt in range(25):
            # start-up the new analysis
            sga = SpacegroupAnalyzer(
                structure,
                symprec=symprec,
                angle_tolerance=angle_tol,
            )

            # For extremely high tolerances, spglib will return None and cause
            # pymatgen to fail with an error. We want to simply move on if
            # an error happens.
            try:
                new_spacegroup = sga.get_space_group_number()
            except TypeError:
                continue

            # We only store the results if we generated a brand-new spacegroup
            if new_spacegroup not in results.keys():
                results.update({new_spacegroup: sga.get_primitive_standard_structure()})

            # For the next cycle, I simple scale the angle and distance tolerances
            # by a fixed percent. This results in the following overall checks:
            #   Ang: 0.11499999999999999, DEG: 0.6
            #   Ang: 0.13224999999999998, DEG: 0.72
            #   Ang: 0.15208749999999996, DEG: 0.864
            #   Ang: 0.17490062499999995, DEG: 1.0368
            #   Ang: 0.20113571874999991, DEG: 1.24416
            #   Ang: 0.23130607656249988, DEG: 1.4929919999999999
            #   Ang: 0.26600198804687486, DEG: 1.7915903999999998
            #   Ang: 0.3059022862539061, DEG: 2.1499084799999997
            #   Ang: 0.35178762919199197, DEG: 2.5798901759999997
            #   Ang: 0.40455577357079076, DEG: 3.0958682111999996
            #   Ang: 0.46523913960640934, DEG: 3.7150418534399994
            #   Ang: 0.5350250105473707, DEG: 4.458050224127999
            #   Ang: 0.6152787621294763, DEG: 5.349660268953598
            #   Ang: 0.7075705764488976, DEG: 6.419592322744317
            #   Ang: 0.8137061629162322, DEG: 7.7035107872931805
            #   Ang: 0.935762087353667, DEG: 9.244212944751816
            #   Ang: 1.0761264004567168, DEG: 11.093055533702179
            #   Ang: 1.2375453605252242, DEG: 13.311666640442615
            #   Ang: 1.4231771646040077, DEG: 15.973999968531137
            #   Ang: 1.6366537392946088, DEG: 19.168799962237365
            #   Ang: 1.8821518001888, DEG: 23.002559954684838
            #   Ang: 2.16447457021712, DEG: 27.603071945621803
            #   Ang: 2.489145755749688, DEG: 33.12368633474616
            #   Ang: 2.8625176191121406, DEG: 39.74842360169539
            symprec *= 1.15
            angle_tol *= 1.2
            # print(f"Ang: {symprec}, DEG: {angle_tol}") --> generates comment above

        # Grab the final & highest symmetry result.
        max_spacegroup = max(list(results.keys()))
        final_structure = results[max_spacegroup]
        # TODO: in the future I could make this a "one_to_many" transformation
        # and return all of the higher-symmetry structures

        # make sure we actually improved the symmetry and didn't just grab
        # the original structure
        if max_spacegroup == original_spacegroup:
            # Failed to generate a higher-symmetry structure
            return

        return final_structure
