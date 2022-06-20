# -*- coding: utf-8 -*-

from simmate.utilities import get_doc_from_readme

__doc__ = get_doc_from_readme(__file__)

from simmate.calculators.vasp.database.relaxation import (
    MatProjRelaxation,
    MatProjIonicStep,
    MITRelaxation,
    MITIonicStep,
    Quality00Relaxation,
    Quality00IonicStep,
    Quality01Relaxation,
    Quality01IonicStep,
    Quality02Relaxation,
    Quality02IonicStep,
    Quality03Relaxation,
    Quality03IonicStep,
    Quality04Relaxation,
    Quality04IonicStep,
    StagedRelaxation,
    MatVirtualLabCINEBEndpointRelaxation,
    MatVirtualLabCINEBEndpointIonicStep,
)

from simmate.calculators.vasp.database.energy import (
    MatProjStaticEnergy,
    MITStaticEnergy,
    Quality04StaticEnergy,
    NEBEndpointStaticEnergy,
)

from simmate.calculators.vasp.database.band_structure import (
    MatProjBandStructure,
)

from simmate.calculators.vasp.database.density_of_states import (
    MatProjDensityOfStates,
)

from simmate.calculators.vasp.database.nudged_elastic_band import (
    MITDiffusionAnalysis,
    MITMigrationHop,
    MITMigrationImage,
)

from simmate.calculators.vasp.database.dynamics import (
    MITDynamicsRun,
    MITDynamicsIonicStep,
)

from simmate.calculators.vasp.database.population_analysis import (
    MatProjBaderAnalysis,
    MatProjBaderELFAnalysis,
)

from simmate.calculators.vasp.database.customized import (
    CustomizedVASPCalculation,
)

from simmate.toolkit.structure_prediction.evolution.database import (
    EvolutionarySearch,
    StructureSource,
)
