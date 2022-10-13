from cluster_expansion import HighQRelaxation, LowQRelaxation, StaticEnergy

from simmate.workflow_engine import Workflow


class ClusterExpansion__Vasp__Staged(Workflow):
    use_database = False

    subworkflows = [
        LowQRelaxation.Relaxation__Vasp__ClusterLowQRelaxation(),
        HighQRelaxation.Relaxation__Vasp__ClusterHighQRelaxation(),
        StaticEnergy.StaticEnergy__Vasp__ClusterStaticEnergy(),
    ]

    @classmethod
    def run_config(cls, command: str, directory: str, structure: str, **kwargs):
        current_task = cls.subworkflows[0]
        state = current_task.run(
            structure=structure,
            command=command,
            directory=directory / current_task.name_full,
        )
        result = state.result(sleep_step=10)

        # The remaining tasks continue and use the past results as an input
        for i, current_task in enumerate(cls.subworkflows[1:]):
            preceding_task = cls.subworkflows[i]  # will be one before because of [:1]
            state = current_task.run(
                structure={
                    "database_table": preceding_task.database_table.table_name,
                    "directory": result["directory"],  # uses preceding result
                    "structure_field": "structure_final",
                },
                # structure=result.to_toolkit() -- in the v0.11.0 release
                command=command,
                directory=directory / current_task.name_full,
            )
            result = state.result(sleep_step=10)

        # we return the final step but update the directory to the parent one
        result["directory"] = directory
        return result
