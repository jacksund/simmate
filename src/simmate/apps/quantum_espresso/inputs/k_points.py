# -*- coding: utf-8 -*-

import math

from pymatgen.core import Lattice

from simmate.toolkit import Structure


class Kpoints:
    # placeholder class until we have general one for both vasp, qe, & others

    def __init__(
        self,
        mode: str,
        grid: list[list[float]] | list[float],
        offset: list[list[float]] | list[float],
        weights: list[list[float]] | list[float],
    ):
        self.mode = mode
        self.grid = grid
        self.offset = offset
        self.weights = weights
        # TODO: maybe add spacing and density attribute for REAL values
        # then original_spacing and original_density as well

    def to_dict(self) -> dict:
        return {
            "mode": self.mode,
            "grid": self.grid,
            "offset": self.offset,
            "weights": self.weights,
        }

    @classmethod
    def from_spacing(
        cls,
        spacing: float,
        lattice: Lattice,
        offset: list[float] = (0, 0, 0),
        gamma_centered: bool = True,
    ):
        """
        Determines the k-point grid needed to achieve *at least* the provided k-point
        spacing (in Angstroms^-1). Spacing is defined as the minimum distance between
        any two k-points. The [a, b, c] grid rounds each value up to the nearest
        integer.

        Results in mode="automatic"
        """
        vectors = lattice.reciprocal_lattice.lengths

        # Calculate the number of k-points in each dimension
        k_points = [math.ceil(v / spacing) for v in vectors]

        # Ensuring an odd number of k-points in Monkhorst-Pack grids helps center
        # one k-point at the Brillouin zone's origin (Γ-point). This is achieved
        # by rounding down to the nearest even number, doubling it, and adding 1,
        # ensuring a well-defined center for accurate Brillouin zone sampling.
        # The convention aids in precise calculations of electronic states near
        # the zone center, contributing to the accuracy of electronic
        # structure calculations.
        if gamma_centered:
            k_points = [(pt // 2) * 2 + 1 for pt in k_points]
        # BUG: I'm not 100% sure this ensures a gamma centered point...
        # ChatGPT gave this suggestion and I'm just rolling with it.
        # This formula often results in a more dense grid than what was requested
        # so I'm sure an offset or something would be better

        return cls(
            mode="automatic",
            grid=k_points,
            offset=offset,
            weights=None,
        )

    @classmethod
    def from_density(
        cls,
        density: float,
        lattice: Lattice,
        **kwargs,
    ):
        """
        Determines the k-point grid needed to achieve *at least* the provided k-point
        density (in Angstroms^-3). The [a, b, c] grid rounds each value up to the
        nearest integer

        Results in mode="automatic"
        """
        spacing = 1 / (density ** (1 / 3))
        return cls.from_spacing(spacing=spacing, lattice=lattice, **kwargs)

    @classmethod
    def from_dynamic(
        cls,
        k_points: any,
        structure: Structure = None,
        lattice: Lattice = None,
    ):
        # TODO: check incorrect configs such as those that have BOTH
        # spacing and denisty. Or provide these with a grid. Or missing a lattice

        if structure:
            lattice = structure.lattice

        if isinstance(k_points, cls):
            return k_points

        elif isinstance(k_points, dict):
            if lattice and "spacing" in k_points:
                return cls.from_spacing(
                    spacing=k_points["spacing"],
                    lattice=lattice,
                )
            elif lattice and "density" in k_points:
                return cls.from_density(
                    density=k_points["density"],
                    lattice=lattice,
                )
            else:
                return cls(**k_points)

        return {}
