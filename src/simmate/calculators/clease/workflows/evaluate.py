#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ase import Atoms
from clease import Evaluate
from clease.settings import CECrystal, Concentration

from simmate.workflow_engine import Workflow


class ClusterExpansion__Python__Evaluate(Workflow):
    use_database = False

    @staticmethod
    def run_config(
        basis_elements: list[list[str]] = [["Al", "Sc"], ["C"], ["Sc", "Al"]],
        # to vary some elements in your CE, use the format <y-x>X<x> and define your x as the threshold of variance
        # for ex. in this we have "C<1>" because we want the concentration to remain constant and we have Al/Sc<1-x>X<x>
        # because we want there to be maximum 2 atoms of one or the other to 1 carbon atom
        formula_unit: list[str] = ["Al<x>Sc<1-x>", "C<1>", "Sc<y>Al<1-y>"],
        variable_range: dict = {"x": (0, 1), "y": (0, 1)},
        atoms: str = "AlScC",
        lattice: list[tuple[float]] = [
            (0.74276, 0.74276, 0.74276),
            (0.0000, 0.0000, 0.0000),
            (0.25724, 0.25724, 0.25274),
        ],
        a: float = 5.78605,
        b: float = 5.78605,
        c: float = 5.78605,
        alph: float = 33.7158,
        beta: float = 33.7158,
        gamma: float = 33.7158,
        db_name: str = "database.db",
        space_group: int = 1,
        supercell: int = 64,  # threshold on max size of supercell
        cluster_diameter: list[int] = [
            7,
            5,
            5,
        ],  # distance between atoms in cluster in angstroms, number of values increase w/ max cluster size
        generationnumber: int = 0,
        structure_per_generation: int = 10,
        **kwargs
    ):

        # define concentration
        conc = Concentration(basis_elements=basis_elements)
        conc.set_conc_formula_unit(formula_unit, variable_range=variable_range)

        # define lattice
        latt = Atoms(atoms, lattice)
        settings = CECrystal(
            concentration=conc,
            spacegroup=space_group,
            cellpar=[a, b, c, alph, beta, gamma],  # data from lattice definition
            supercell_factor=supercell,
            basis=latt.get_positions(),
            db_name=db_name,
            max_cluster_dia=cluster_diameter,
        )

        eva = Evaluate(settings=settings, scoring_scheme="loocv")
        # scan different values of alpha and return the value of alpha that yields
        # the lowest CV score
        # alpha is the regularization parameter designed to penalize model complexity
        # higher the alpha, less complex model, decreasing error due to variance
        # alphas that are too high increase error due to bias (underfit)
        eva.set_fitting_scheme(fitting_scheme="l1")
        alpha = eva.plot_CV(
            alpha_min=1e-7, alpha_max=1.0, num_alpha=50, savefig=True, fname="CV.png"
        )
        # set the alpha value with the one found above, and fit data using it.
        eva.set_fitting_scheme(fitting_scheme="l1", alpha=alpha)
        eva.plot_fit(interactive=False, savefig=True, fname="Energies.png")
        # plot ECI values
        eva.plot_ECI()
        # save eci values into json
        eva.save_eci(fname="eci_H1_l1")
