# -*- coding: utf-8 -*-

from django.apps import AppConfig


class AnalysisDashboardConfig(AppConfig):
    name = "simmate.apps.dev.analysis_dashboard"
    verbose_name = "Analysis Dashboard"
    description_short = (
        "A dashboard for analyzing general datasets with dynamic and interactive plots"
    )


class BioviaCosmoConfig(AppConfig):
    name = "simmate.apps.dev.biovia_cosmo"


class ChatbotConfig(AppConfig):
    name = "simmate.apps.dev.chatbot"


class CleaseConfig(AppConfig):
    name = "simmate.apps.dev.clease"


class DeepmdConfig(AppConfig):
    name = "simmate.apps.dev.deepmd"


class EtherscanConfig(AppConfig):
    name = "simmate.apps.dev.etherscan"


class OpeneyeOmegaConfig(AppConfig):
    name = "simmate.apps.dev.openeye_omega"


class PriceCatalogConfig(AppConfig):
    name = "simmate.apps.dev.price_catalog"


class ProjectManagementConfig(AppConfig):
    name = "simmate.apps.dev.project_management"


class SchrodingerConfig(AppConfig):
    name = "simmate.apps.dev.schrodinger"


class SurflexConfig(AppConfig):
    name = "simmate.apps.dev.surflex"
