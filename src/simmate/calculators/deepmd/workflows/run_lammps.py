# -*- coding: utf-8 -*-
"""
Created on Mon Oct 24 11:45:11 2022

@author: siona
"""

from pathlib import Path

from pymatgen.io.lammps.data import LammpsData

from simmate.toolkit import Structure
from simmate.workflow_engine import S3Workflow

# steps for running lammps:
# create datafile for starting structure
# write input file
# submit lammps run

#!!! switch to deepmd environment to use lammps?
#!!! lammps vs lammps-dp??


class MlPotential__Deepmd__RunLammps(S3Workflow):

    use_database = False  # add database???
    monitor = False
    command = "lmp -in in.lmp"  # need mpi run part???

    def setup(
        structure: Structure,  # structure to run lammps with
        directory: Path,  # directory of lammps run
        data_filename: str = "data.lmp",
        input_filename: str = "in.lmp",
        deepmd_model: str = "graph.pb",
        lammps_temp: int = 300,
        lammps_timestep: int = 100000,
        lammps_dump_filename: str = "dump.lammpstrj",
    ):


        ldata = LammpsData.from_structure(structure=structure, atom_style="atomic")

        ldata.write_file(filename=directory / data_filename)

        # write input file

        input_list = [
            "#simulation settings",
            "units metal",
            "boundary ppp",
            "atom_style atomic",
            "neighbor 2.0 bin",
            "neigh_modify every 10 delay 0 check no",
            "#import structure",
            f"read_data {data_filename}",
            "#force_field",
            f"pair_style deepmd {deepmd_model}",
            "pair_coeff **",
            "# write out trajectories of atoms",
            f"dump TRAJ all custom 10 {lammps_dump_filename} id element x y z",
            "dump_modify TRAJ element C",  # change C to list of elements???
            "# how often to write information to log file",
            "thermo_style custom step cpu etotal ke pe evdwl ecoul elong temp press vol density",
            "thermo 10",
            "# relax initial structure",
            "minimize 1.0e-30 1.0e-30 500 500",
            "reset_timestep 0",
            "# amount of time that each timestep represents, in units of picoseconds",
            "timestep 0.0002",
            "# temperature and pressure",
            f"variable TK1 equal {lammps_temp}",
            "variable PBAR equal 1.0",
            "#initialize velocities of atoms",
            "velocity        all create ${TK1} 83829102 rot yes mom yes dist gaussian",
            "# npt = constant mass, pressure and temperature",
            "fix TPSTAT all npt temp ${TK1} ${TK1} 5 iso ${PBAR} ${PBAR} 20",
            "# run the simulation for this many timesteps",
            f"run {lammps_timestep}",
        ]

        input_file = directory / input_filename
        with input_file.open("w") as file:
            for line in input_list:
                file.write(line)
                file.write("\n")
