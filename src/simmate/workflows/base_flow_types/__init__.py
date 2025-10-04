# -*- coding: utf-8 -*-

from .base import Workflow
from .pg_dump import Maintenance__Postgres__PgDump
from .s3 import S3Workflow
from .staged import StagedWorkflow
from .structure_input import StructureWorkflow
from .web_api import WebApiWorkflow
