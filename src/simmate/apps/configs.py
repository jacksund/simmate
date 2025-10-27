# -*- coding: utf-8 -*-

from django.apps import AppConfig


class AflowConfig(AppConfig):
    name = "simmate.apps.aflow"


class AnalysisDashboardConfig(AppConfig):
    name = "simmate.apps.analysis_dashboard"
    verbose_name = "Analysis Dashboard"
    description_short = (
        "A dashboard for analyzing general datasets with dynamic and interactive plots"
    )


class BadelfConfig(AppConfig):
    name = "simmate.apps.badelf"


class BaderConfig(AppConfig):
    name = "simmate.apps.bader"

class BaderkitConfig(AppConfig):
    name = "simmate.apps.baderkit"

class BcpcConfig(AppConfig):
    name = "simmate.apps.bcpc"


class BioviaCosmoConfig(AppConfig):
    name = "simmate.apps.biovia_cosmo"


class CasRegistryConfig(AppConfig):
    name = "simmate.apps.cas_registry"


class ChatbotConfig(AppConfig):
    name = "simmate.apps.chatbot"


class ChemblConfig(AppConfig):
    name = "simmate.apps.chembl"


class ChemspaceConfig(AppConfig):
    name = "simmate.apps.chemspace"


class CleaseConfig(AppConfig):
    name = "simmate.apps.clease"


class CodConfig(AppConfig):
    name = "simmate.apps.cod"


class DeepmdConfig(AppConfig):
    name = "simmate.apps.deepmd"


class EmoleculesConfig(AppConfig):
    name = "simmate.apps.emolecules"


class EnamineConfig(AppConfig):
    name = "simmate.apps.enamine"


class EppoGdConfig(AppConfig):
    name = "simmate.apps.eppo_gd"


class EtherscanConfig(AppConfig):
    name = "simmate.apps.etherscan"


class EvolutionConfig(AppConfig):
    name = "simmate.apps.evolution"


class JarvisConfig(AppConfig):
    name = "simmate.apps.jarvis"


class MaterialsProjectConfig(AppConfig):
    name = "simmate.apps.materials_project"


class OpeneyeOmegaConfig(AppConfig):
    name = "simmate.apps.openeye_omega"


class OqmdConfig(AppConfig):
    name = "simmate.apps.oqmd"


class PdbConfig(AppConfig):
    name = "simmate.apps.pdb"


class PpdbConfig(AppConfig):
    name = "simmate.apps.ppdb"


class PriceCatalogConfig(AppConfig):
    name = "simmate.apps.price_catalog"


class ProjectManagementConfig(AppConfig):
    name = "simmate.apps.project_management"


class QuantumEspressoConfig(AppConfig):
    name = "simmate.apps.quantum_espresso"


class RdkitConfig(AppConfig):
    name = "simmate.apps.rdkit"


class SchrodingerConfig(AppConfig):
    name = "simmate.apps.schrodinger"


class SurflexConfig(AppConfig):
    name = "simmate.apps.surflex"


class VaspConfig(AppConfig):
    name = "simmate.apps.vasp"


class WarrenLabConfig(AppConfig):
    name = "simmate.apps.warren_lab"
