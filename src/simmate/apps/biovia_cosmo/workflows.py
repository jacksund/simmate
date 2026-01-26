# -*- coding: utf-8 -*-

# USER NOTE: Make sure you have "biovia_cosmo.zip" unpacked into ~/simmate dir.
# In the future, maybe I can grab this in a better way.

import shutil
from pathlib import Path

from simmate.apps.biovia_cosmo.models import LogPow as LogPowTable
from simmate.configuration import settings
from simmate.toolkit import Molecule
from simmate.workflows import Workflow
from simmate.workflows.base_flow_types import S3Workflow

__all__ = [
    "ConformerGeneration__CosmoConf__BpSvpAm1",
    "ConformerGeneration__CosmoConf__Tzvp",
    "ConformerGeneration__CosmoConf__TzvpFine",
    "Solubility__CosmoTherm__LogPowFromCtdPreset",
    "Solubility__BioviaCosmo__LogPowBpSvpAm1",
    "Solubility__BioviaCosmo__LogPowTzvp",
    "Solubility__BioviaCosmo__LogPowTzvpFine",
]


# -----------------------------------------------------------------------------

# STEP 1: CosmoConf (+Turbomol) conformer generation, relaxtion, & static energy calc
# We have multiple subworkflows to help organize different settings in the database


class CosmoConf(S3Workflow):
    command = "cosmoconf.pl -l input.txt -m {ctd_preset} > cosmoconf.out"  # -np 20
    required_files = ["input.txt", "molecule.sdf"]
    monitor = False
    use_database = False

    preset: str = None
    """
    Common parameterization presets that control the quality at which CosmoConf
    is ran. Options are:

        - BP-SVP-AM1-COSMO+GAS
        - BP-TZVP-COSMO+GAS_18
        - BP-TZVPD-FINE-COSMO+GAS_18
        - DMOL3-PBE-COSMO+GAS

    These are set by the workflows inheriting from this base class.
    """

    @staticmethod
    def setup(
        molecule: Molecule,
        directory: Path,
        **kwargs,
    ):
        # Write the 3D molecule file
        molecule.convert_to_3d(keep_hydrogen=True)
        molecule.to_sdf_file(filename=directory / "molecule.sdf")

        # Write the input.txt file, which is always the same. It lists off
        # molecules to run, where we only have the one file for now.
        input_file = directory / "input.txt"
        with input_file.open("w") as file:
            file.write("molecule.sdf")


class ConformerGeneration__CosmoConf__BpSvpAm1(CosmoConf):
    command = "cosmoconf.pl -l input.txt -m BP-SVP-AM1-COSMO+GAS > cosmoconf.out"
    preset = "BP-SVP-AM1-COSMO+GAS"


class ConformerGeneration__CosmoConf__Tzvp(CosmoConf):
    command = "cosmoconf.pl -l input.txt -m BP-TZVP-COSMO+GAS_18 > cosmoconf.out"
    preset = "BP-TZVP-COSMO+GAS_18"


class ConformerGeneration__CosmoConf__TzvpFine(CosmoConf):
    command = "cosmoconf.pl -l input.txt -m BP-TZVPD-FINE-COSMO+GAS_18 > cosmoconf.out"
    preset = "BP-TZVPD-FINE-COSMO+GAS_18"


# -----------------------------------------------------------------------------

# STEP 2: CosmoTherm LogPow prediction using step 1 output


class Solubility__CosmoTherm__LogPowFromCtdPreset(S3Workflow):
    command = "cosmotherm cosmotherm.inp"
    required_files = ["cosmotherm.inp"]
    monitor = False
    use_database = False

    @staticmethod
    def setup(
        # typically from a ConformerGeneration__CosmoConf__BpSvpAm1 output
        cosmoconf_dir: str | Path,
        directory: Path,
        ctd_preset: str,  # options are listed inthe preset_dir (e.g. "BP_SVP_AM1_22")
        # Default config directories
        # solvent_db_dir: str="/share/apps/cosmotherm/2022/COSMOtherm/DATABASE-COSMO/BP-SVP-AM1",
        preset_dir: str = "/share/apps/cosmotherm/2022/COSMOtherm/CTDATA-FILES",
        license_dir: str = "/share/apps/cosmotherm/2022/licensefiles",
        **kwargs,
    ):
        # Copy all files from the cosmo directories to here
        # OPTIMIZE: Is there a way to set multiple fdir locations? One for the
        # octanol+h2o and the other for inputs of this calc
        molecule_dir = directory / "input_molecules"
        shutil.copytree(
            src=cosmoconf_dir,
            dst=molecule_dir,
            dirs_exist_ok=True,
        )
        shutil.copytree(
            src=settings.config_directory / "biovia_cosmo" / ctd_preset,
            dst=molecule_dir,
            dirs_exist_ok=True,
        )

        # This section pulls together all molecules listed and writes them
        # in the cosmotherm input format. Results will look like this:
        # f=phenol_c0   pk_acid=9.8
        # [ f=2-chlorophenol_c0
        #   f=2-chlorophenol_c1 ]
        cosmoconf_dir = Path(cosmoconf_dir)
        molecule_names = [
            file.stem for file in cosmoconf_dir.iterdir() if file.suffix == ".cosmo"
        ]
        molecule_names.sort()
        if len(molecule_names) <= 0:
            raise Exception("At least one *.cosmo input file is required")
        elif len(molecule_names) == 1:
            molecule_input_txt = molecule_names[0]
        elif len(molecule_names) >= 0:
            text = "".join([f" f={n} \n " for n in molecule_names])[:-2]
            molecule_input_txt = f"[{text}]"

        ###### BUG-CHECK
        # I assume only a single molecule with all of its conformers is present
        for n in molecule_names:
            assert "molecule_" in n
        ######

        input_text = COSMOTHERM_INP_TEMPLATE.format(**locals())
        input_file = directory / "cosmotherm.inp"
        with input_file.open("w") as file:
            file.write(input_text)

    @staticmethod
    def workup(directory: Path):
        # For now, I just grab the final molecule's log P value, which is
        # the last number listed in this tab file.
        filename = directory / "cosmotherm.tab"
        with filename.open("r") as file:
            text = file.read()
        log_p = float(text.split()[-1])
        # BUG: This step will need updated if I add pKa or multiple molecules
        return {"log_p": log_p}


# -----------------------------------------------------------------------------

# STEP 3: Piecing together steps 1+2 into a larger workflow.
# This is the workflow that we submit for each molecule.


class BioviaCosmo(Workflow):
    database_table = LogPowTable

    preset: str = None
    """
    Common parameterization presets that control the quality at which CosmoConf
    is ran. Options are:

        - BP-SVP-AM1-COSMO+GAS
        - BP-TZVP-COSMO+GAS_18
        - BP-TZVPD-FINE-COSMO+GAS_18
        - DMOL3-PBE-COSMO+GAS

    These are set by the workflows inheriting from this base class.
    """

    _preset_mappings = {
        "BP-SVP-AM1-COSMO+GAS": {
            "cosmoconf_workflow": ConformerGeneration__CosmoConf__BpSvpAm1,
            "cosmoconf_subdir": "Results_of_job_BP-SVP-AM1-COSMO+GAS",
            "cosmotherm_preset": "BP_SVP_AM1_22",
        },
        "BP-TZVP-COSMO+GAS_18": {
            "cosmoconf_workflow": ConformerGeneration__CosmoConf__Tzvp,
            "cosmoconf_subdir": "Results_of_BP-TZVP-COSMO",
            "cosmotherm_preset": "BP_TZVP_22",
        },
        "BP-TZVPD-FINE-COSMO+GAS_18": {
            "cosmoconf_workflow": ConformerGeneration__CosmoConf__TzvpFine,
            "cosmoconf_subdir": "Results_of_BP-TZVPD-FINE-COSMO",
            "cosmotherm_preset": "BP_TZVPD_FINE_22",
        },
    }
    """
    Given a preset name, this points to the proper cosmoconf workflow
    and it's corresponding cosmotherm ctd_preset. This is used within the
    run_config and should not be modified by the user.
    """

    @classmethod
    def run_config(
        cls,
        molecule: Molecule,
        directory: Path,
        **kwargs,
    ):
        # pull the proper subworkflows from the preset mapppings (see attribute
        # that sets these above)
        cosmoconf_workflow, cosmoconf_subdir, cosmotherm_preset = cls._preset_mappings[
            cls.preset
        ].values()

        cosmoconf_dir = directory / cosmoconf_workflow.name_full
        cosmoconf_workflow.run(
            molecule=molecule,
            directory=cosmoconf_dir,
        )

        cosmotherm_dir = (
            directory / Solubility__CosmoTherm__LogPowFromCtdPreset.name_full
        )
        log_p_dict = Solubility__CosmoTherm__LogPowFromCtdPreset.run(
            cosmoconf_dir=cosmoconf_dir / cosmoconf_subdir,
            ctd_preset=cosmotherm_preset,
            directory=cosmotherm_dir,
        )

        return log_p_dict


class Solubility__BioviaCosmo__LogPowBpSvpAm1(BioviaCosmo):
    preset = "BP-SVP-AM1-COSMO+GAS"


class Solubility__BioviaCosmo__LogPowTzvp(BioviaCosmo):
    preset = "BP-TZVP-COSMO+GAS_18"


class Solubility__BioviaCosmo__LogPowTzvpFine(BioviaCosmo):
    preset = "BP-TZVPD-FINE-COSMO+GAS_18"


# -----------------------------------------------------------------------------

# EXTRAS: (e.g. input file templates)

COSMOTHERM_INP_TEMPLATE = """# CosmoTherm input made by Simmate
###################################
# SECTION 1: global variables for program configuration
ctd={ctd_preset}.ctd
@ cdir={preset_dir}
@ ldir={license_dir}
@ fdir={molecule_dir}
! Automatic logD (Octanol-Water Partition Coefficient with Dissociation Correction)
###################################
# SECTION 2: input molecule files
# solvent 1 (water)
f=h2o_c0
# solvent 2 (octanol)
[ f=1-octanol_c0
  f=1-octanol_c1 ]
# user-input molecule
{molecule_input_txt}
##################################
# SECTION 3: calculation parameters
tc=25
@ logp={{1 2}}
@ xl1={{1 0}}
@ xl2={{0.274 0.726}}
@ vq=0.1505
@ pH=7.4
###################################
"""
# NOTES ON SECTION 3 IN INPUT ABOVE
# These comments are from...
# tc=25             - temperature in deg Celcius
# logp={1 2}        - automatic logP computation between solvents 1 (h2o) and 2 (1-octanol)
#                     See COSMOtherm user manual section 2.3.5.
# xl1={1 0}         - mole fraction concentration of solvent 1 (h2o)
#                     i.e. pure water is used
# xl2={0.274 0.726} - mole fraction concentration of solvent 2 (1-octanol)
#                     i.e. octanol phase (wet octanol) with x_h2o=0.274 and x_oct=0.726
#                     (A. Dallos, J. Liszi, J. Chem. Thermodynamics, 27 (1995) 447-448).
# vq=0.1505         - experimental volume quotient between water phase and octanol (wet) phase
#                     (A. Dallos, J. Liszi, J. Chem. Thermodynamics, 27 (1995) 447-448).
# pH=7.4            - pH value of the solution (in pharmaceutical measurement of logD typically
#                     a buffered water solution of pH=7.4 is used, not neutral water pH=7.0)
# comp_acid={n i}   - toggle cosmotherm pKa(ACID) prediction for solute n. This option
#                     requires that in addition to solute n the ANION (compound i) of
#                     the solute is given in the compound list and given in the input.
#                     the pka value estimated with the help of solute n and its anion i
#                     will be used in the dissociation correction to logPOW
# comp_base={n i}   - toggle cosmotherm pKa(BASE) prediction for solute n. This option
#                     requires that in addition to solute n the CATION (compound i) of
#                     the solute is given in the compound list and given in the input.
#                     the pka value estimated with the help of solute n and its cation i
#                     will be used in the dissociation correction to logPOW
#
# Please note that the computation of logD (i.e. the dissociation correction to a Partition
# Coefficient) is possible only for partitions of systems with one water phase (such as logPOW).
# See section 2.3.5 of the COSMOtherm User's Manual for further details on logD.
