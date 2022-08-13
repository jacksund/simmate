# -*- coding: utf-8 -*-


class StructurePrediction__Python__NewIndividual(Workflow):

    use_database = False

    @classmethod
    def run_config(
        search_id: int,
        nfirst_generation: int,
    ):

        search_datatable = EvolutionarySearch.object.get(id=search_id)

        is_transformation = True

        # transformations from a database table require that we have
        # completed structures in the database. We want to wait until there's
        # a set amount before we start mutating the best. We check that here.
        if is_transformation and (
            search_datatable.individuals_completed.count() < nfirst_generation
        ):
            logging.info(
                "Search isn't ready for transformations yet."
                f" Skipping {self.__class__.__name__}."
            )
            return False, False
        # TODO -- this section will likely be at a higher level.

    def _check_steadystate_workflows(self):

        # we iterate through each steady-state source and check to see how many
        # jobs are still running for it. If it's less than the target steady-state,
        # then we need to submit more!
        for source, source_db, njobs_target in zip(
            self.steadystate_sources,
            self.steadystate_sources_db,
            self.steadystate_source_counts,
        ):
            # This loop says for the number of steady state runs we are short,
            # create that many new individuals! max(x,0) ensure we don't get a
            # negative value. A value of 0 means we are at steady-state and can
            # just skip this loop.
            for n in range(max(int(njobs_target - source_db.nflow_runs), 0)):

                # now we need to make a new individual and submit it!
                parent_ids, structure = self._make_new_structure(source)

                # sometimes we fail to make a structure with the source. In cases
                # like this, we warn the user, but just move on. This means
                # we will be short of our steady-state target. The warning for
                # this is done inside _make_new_structure
                if not structure:
                    break

                # submit the structure workflow
                # Note, we only pass the workflow_command if it's been supplied.
                extra_kwargs = (
                    {"command": self.workflow_command} if self.workflow_command else {}
                )
                state = self.workflow.run_cloud(
                    structure=structure,
                    tags=self.tags,
                    **extra_kwargs,
                )

                # Attached the id to our source so we know how many
                # associated jobs are running.
                # NOTE: this is the WorkItem id and NOT the run_id!!!
                source_db.run_ids.append(state.pk)
                source_db.save()

                # update the source on the calculation
                # TODO: use the flow run id from above to grab the calc
                calculation = self.calculation_datatable.objects.get(
                    run_id=state.run_id
                )
                calculation.source = {
                    "creator": f"{source.__class__.__name__}",
                    "parent_ids": parent_ids,
                }
                calculation.save()
