# -*- coding: utf-8 -*-

from pymatgen.io.vasp.inputs import Kpoints
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
from pymatgen.symmetry.bandstructure import HighSymmKpath


def get_hse_kpoints(
    structure,
    added_kpoints: list = [],
    mode="line",  # or uniform
    reciprocal_density: float = 50,
    kpoints_line_density: float = 20,
):
    # TODO: move these options up to setup() so they can be set in the yaml file
    # BUGFIX:
    #   https://github.com/jacksund/simmate/issues/388
    # This code is copied and modified from...
    #   https://github.com/materialsproject/pymatgen/blob/b4fb2593dc0d0f1d2de7e3bb88ed0b0e1d039733/pymatgen/io/vasp/sets.py#L1376-L1421
    kpts: list[int | float | None] = []
    weights: list[float | None] = []
    all_labels: list[str | None] = []

    # for both modes, include the Uniform mesh w/standard weights
    grid = Kpoints.automatic_density_by_vol(structure, reciprocal_density).kpts
    ir_kpts = SpacegroupAnalyzer(structure, symprec=0.1).get_ir_reciprocal_mesh(grid[0])
    for k in ir_kpts:
        kpts.append(k[0])
        weights.append(int(k[1]))
        all_labels.append(None)

    # for both modes, include any user-added kpoints w/zero weight
    for k in added_kpoints:
        kpts.append(k)
        weights.append(0.0)
        all_labels.append("user-defined")

    # for line mode only, add the symmetry lines w/zero weight
    if mode.lower() == "line":
        kpath = HighSymmKpath(structure)
        frac_k_points, labels = kpath.get_kpoints(
            line_density=kpoints_line_density,
            coords_are_cartesian=False,
        )

        for k, f in enumerate(frac_k_points):
            kpts.append(f)
            weights.append(0.0)
            all_labels.append(labels[k])

    comment = (
        "HSE run along symmetry lines"
        if mode.lower() == "line"
        else "HSE run on uniform grid"
    )

    return Kpoints(
        comment=comment,
        style=Kpoints.supported_modes.Reciprocal,
        num_kpts=len(kpts),
        kpts=kpts,  # type: ignore
        kpts_weights=weights,
        labels=all_labels,
    )
