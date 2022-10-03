# -*- coding: utf-8 -*-

import logging

import numpy
import scipy
from django.utils import timezone
from rich.progress import track

from simmate.toolkit import Structure
from simmate.toolkit.validators import Validator


class FingerprintValidator(Validator):

    comparison_mode: str = "linalg_norm"
    """
    How fingerprints distances should be determined. Options are:
        - linalg_norm
        - cos
        - custom

    For 'custom', you must write a custom 'get_fingerprint_distance(fp1, fp2)'
    static method that will be used.
    """

    def __init__(
        self,
        distance_tolerance: float = 0.001,
        structure_pool: list[Structure] = [],  # OR a queryset from a Structure table
        **kwargs,
    ):

        self.distance_tolerance = distance_tolerance

        # setup featurizer with the given composition
        self.featurizer = self.get_featurizer(**kwargs)

        # check if we were given a list of pymatgen structures.
        if isinstance(structure_pool, list):

            # If so, we generate the fingerprint for each of the initial input structures
            # We convert this to a numpy array for speed improvement at later stages
            self.fingerprint_pool = numpy.array(
                [
                    self._get_fingerprint(structure)
                    for structure in track(structure_pool)
                ]
            )
            # OPTIMIZE: this can be slow and I should support parallel featurization.

            # populate the source_pool and order_by_pool with values. These
            # will be in the same order as the fingerprints
            self.source_pool = [structure.source for structure in structure_pool]

            # When the database isn't being used, we still need set these
            # variable as none to help with some other methods.
            self.structure_pool_queryset = "local_only"

        # otherwise we have a queryset that should be used to populate the
        # fingerprint database
        else:
            # The fingerprint database table can store many different
            # fingerprints -- both from different fingerprint featurizers AND
            # using different settings for a given featurizer. We therefore
            # need to store the init kwargs with each fingerprint in the database
            from simmate.workflow_engine import Workflow

            self.init_kwargs = Workflow._serialize_parameters(
                distance_tolerance=distance_tolerance,
                **kwargs,
            )
            # TODO: _serialize_parameters should be a utility and not
            # attached to the workflow class

            # we store the queryset as an attribute because we may want to
            # update the structure pool later on.
            self.structure_pool_queryset = structure_pool
            self.fingerprint_pool = numpy.array([])
            self.source_pool = []

            # we also keep a log of the last update so we only grab new structures
            # each time we update the database. To start, we set this as the
            # eariest possible date, which tells our update_fingerprint_pool
            # method to include ALL structures
            self.last_update = timezone.make_aware(
                timezone.datetime.min, timezone.get_default_timezone()
            )
            self.update_fingerprint_pool()

    # -------------------------------------------------------------------------
    # Methods that can be overwritten when creating a new subclass
    # -------------------------------------------------------------------------

    @staticmethod
    def get_featurizer(self, **kwargs):
        raise NotImplementedError(
            "make sure you add a custom 'get_featurizer' method. This should "
            "return a featurizer object to be used for generating fingerprints."
        )

    def get_fingerprint_distance(self, fingerprint1, fingerprint2) -> float:
        raise NotImplementedError(
            "If you set the class attribute 'comparison_mode' to 'custom', make "
            "sure you also add a custom 'get_fingerprint_distance' method. This "
            "should return a distance (float value) ."
        )

    @staticmethod
    def format_fingerprint(fingerprint):
        return fingerprint  # does nothing by default

    # -------------------------------------------------------------------------
    # Core methods that generate and compare fingerprints
    # -------------------------------------------------------------------------

    def check_structure(
        self,
        structure: Structure,
        add_unique_to_pool: bool = True,
        store_in_database: bool = True,  # only if structures have database_object attribute
    ):

        # TODO:
        # maybe add a check to see if a matching source is already in the
        # the source_pool.

        # make the fingerprint
        fingerprint1 = self._get_fingerprint(structure)

        # compare this new fingerprint to all others
        is_unique = self._check_fingerprint(fingerprint1, self.fingerprint_pool)

        # add this new fingerprint to the database if it was requested.
        if is_unique and add_unique_to_pool:

            # BUG-FIX:
            # in case a pymatgen structure was given, set the source to {}
            if not hasattr(structure, "source"):
                structure.source = {}

            self._add_to_pool(fingerprint1, structure.source)

        # as an extra, we save the result to our database so that this
        # fingerprint doesn't need to be calculated again
        if store_in_database and hasattr(structure, "database_object"):
            self._add_to_database(structure, fingerprint1)

        # Return that we were successful
        return is_unique

    def _check_fingerprint(
        self,
        fingerprint1: numpy.array,
        fingerprint_pool: list[numpy.array],
    ):

        # We now want to get the distance of this fingerprint relative to all others.
        # If the distance is within the specified tolerance, then the structures
        # are too similar - and we return  for a failure.
        is_unique = True  # consider it unique until proven otherwise
        for fingerprint2 in fingerprint_pool:

            # check fingerprint based on the mode set
            if self.comparison_mode == "linalg_norm":
                distance = numpy.linalg.norm(fingerprint1 - fingerprint2)
            elif self.comparison_mode == "cos":
                distance = scipy.spatial.distance.cosine(fingerprint1, fingerprint2)
            elif self.comparison_mode == "custom":
                distance = self.get_fingerprint_distance(fingerprint1, fingerprint2)
            else:
                raise NotImplementedError("Unknown comparison_mode provided.")

            # and determine if we have a match
            if distance < self.distance_tolerance:
                # we can end the whole for-loop as soon as one structure is
                # deemed too similar
                is_unique = False
                break

        # If we make it through all structures and no distance is below the
        # tolerance, then we have a new and unique fingerprint

        return is_unique

    def _get_fingerprint(self, structure: Structure):
        # make the fingerprint for this structure into a numpy array for speed
        fingerprint = numpy.array(self.featurizer.featurize(structure))

        # apply any extra formatting
        fingerprint = self.format_fingerprint(fingerprint)

        return fingerprint

    # -------------------------------------------------------------------------
    # Methods that populate the pool and database with information
    # -------------------------------------------------------------------------

    def update_fingerprint_pool(self, use_fp_database: bool = True):

        if self.structure_pool_queryset == "local_only":
            raise Exception(
                "This method should only be used when your structure pool"
                " is based on a Simmate database table!"
            )

        # what if a structure was added to the table WHILE I was running the
        # last query? This sets up a race condition with new structures and my
        # last_update timestamp. To avoid this, I immediately update our
        # timestamp, rather than doing it after the query
        last_update_safe = self.last_update
        self.last_update = timezone.now()

        # Now grab all the new structure ids that need to be added to the database
        new_ids = self.structure_pool_queryset.filter(
            created_at__gte=last_update_safe
        ).values_list("id", flat=True)

        # If there aren't any new structures, just exit without printing the
        # message and progress bar
        if not new_ids:
            return

        # first we can check if these structures have fingerprints already
        # calculated and load those.
        if use_fp_database:
            logging.info("Checking database for already-calculated fingerprints")

            from simmate.database.base_data_types import Fingerprint

            query = (
                Fingerprint.objects.filter(
                    source__database_table=self.structure_pool_queryset.model.table_name,
                    source__database_id__in=list(new_ids),
                )
                .distinct("source__database_id")
                .all()
            )
            # BUG: somehow a database_id single database id is being store multiple
            # times (4 times it looks like?), which makes this query much larger
            # than it should be -- and slower/less stable. I think this is because
            # the fingerprint is added at structure creation AND at the end
            # of the static energy search. There might also be race conditions.

            # the query does not return the ids in the same order that new_ids
            # was given. Order is important when finding unique structures, so
            # we need to reorder the query results here
            all_data_dict = {entry.source["database_id"]: entry for entry in query}
            all_data_ordered = [
                all_data_dict[id] for id in new_ids if id in all_data_dict.keys()
            ]

            for entry in all_data_ordered:
                self._add_to_pool(entry.fingerprint, entry.source)

            # reset the new_structures list to those that are actually still needed
            existing_ids = [fp.source["database_id"] for fp in query]
            new_ids = [i for i in new_ids if i not in existing_ids]

        # same as before -- exit if there aren't any new ids
        if not new_ids:
            return

        logging.info(f"Found {len(new_ids)} new structure(s) for the fingerprint pool.")

        new_structures = self.structure_pool_queryset.filter(
            id__in=new_ids
        ).to_toolkit()

        # OPTIMIZE: I attempted to calculate fingerprints with Dask, but without
        # any luck. Ends up crashing in many scenarios.
        # from simmate.configuration.dask import get_dask_client
        # with get_dask_client() as client:
        #     futures = [client.submit(self._get_fingerprint, s) for s in new_structures]
        #     fingerprints = [future.result() for future in track(futures)]

        # calculate each fingerprint and add it to the database
        for structure in track(new_structures):
            fingerprint = self._get_fingerprint(structure)
            self._add_to_pool(fingerprint, structure.source)

            # OPTIMIZE: this can be faster if done in one query
            if use_fp_database:
                self._add_to_database(structure, fingerprint)

    def _add_to_pool(self, fingerprint, source: dict = {}):

        # source
        self.source_pool.append(source)

        # fingerprint
        # Numpy arrays begin differently when empty
        if self.fingerprint_pool.size == 0:
            self.fingerprint_pool = numpy.array([fingerprint])
        else:
            self.fingerprint_pool = numpy.append(
                self.fingerprint_pool, [fingerprint], axis=0
            )

    def _add_to_database(self, structure, fingerprint):
        from simmate.database.base_data_types import Fingerprint

        new_fp = Fingerprint(
            method=self.name,
            init_kwargs=self.init_kwargs,
            source=structure.source,
            fingerprint=list(fingerprint),
        )
        new_fp.save()

    # -------------------------------------------------------------------------
    # Extra high level methods that are useful for analyzing a structure pool
    # -------------------------------------------------------------------------

    def remove_duplicates(self, structures: list[Structure]) -> list[Structure]:
        raise NotImplementedError("This method is still under development")
        # This might need to be a class method because I don't want to use
        # an already existing fingerprint_pool
        structures_unique = []
        for structure in track(structures):
            if self.check_structure(structure):
                structures_unique.append(structure)

    def get_unique_from_pool(self) -> list[Structure]:

        # order of the input structures is important for this method
        if (
            self.structure_pool_queryset
            and not self.structure_pool_queryset.query.order_by
        ):
            logging.warning(
                "The order of your structures is important. You should set "
                "order_by('some_column') on your database search. If duplicates "
                " are found, only the first structure will be returned."
            )

        logging.info("Isolating unique structures")

        # The first structure in our pool is unique by default so this
        # starts out our list
        unique_sources = [self.source_pool[0]]
        unique_fingerprints = numpy.array([self.fingerprint_pool[0]])

        # The rest need to be checked one at a time
        for source, fingerprint in track(
            list(zip(self.source_pool, self.fingerprint_pool))
        ):
            is_unique = self._check_fingerprint(
                fingerprint,
                unique_fingerprints,
            )
            if is_unique:
                unique_sources.append(source)
                unique_fingerprints = numpy.append(
                    unique_fingerprints, [fingerprint], axis=0
                )

        logging.info(
            f"{len(unique_sources)} unique entries found. "
            "Pulling structures from database."
        )

        # collect the unique sources so that we can make a single query.
        from simmate.file_converters.structure.database import DatabaseAdapter

        structures = DatabaseAdapter.get_toolkits_from_database_dicts(unique_sources)

        return structures
