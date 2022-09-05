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
        add_unique_to_pool: bool = True,
        **kwargs,
    ):

        # OPTIMIZE: my choice of tolerance is based on my evolutionary search.
        # However, "clustering" after evolutionary search suggests that something
        # like 0.5 might be a better choice for finding a truly unique structure
        self.distance_tolerance = distance_tolerance

        self.add_unique_to_pool = add_unique_to_pool

        # setup featurizer with the given composition
        self.featurizer = self.get_featurizer(**kwargs)

        # check if we were given a list of pymatgen structures.
        if isinstance(structure_pool, list):
            # set this variable as none to help with some warnings methods such
            # as the update_fingerprint_database
            self.structure_pool_queryset = "local_only"
            # If so, we generate the fingerprint for each of the initial input structures
            # We convert this to a numpy array for speed improvement at later stages
            # OPTIMIZE: this can be slow and I should support parallel featurization
            self.fingerprint_database = numpy.array(
                [
                    self.featurizer.featurize(structure)
                    for structure in track(structure_pool)
                ]
            )

        # otherwise we have a queryset that should be used to populate the
        # fingerprint database
        else:
            # we store the queryset as an attribute because we may want to
            # update the structure pool later on.
            self.structure_pool_queryset = structure_pool
            self.fingerprint_database = numpy.array([])
            # we also keep a log of the last update so we only grab new structures
            # each time we update the database. To start, we set this as the
            # eariest possible date, which tells our update_fingerprint_database
            # method to include ALL structures
            self.last_update = timezone.make_aware(
                timezone.datetime.min, timezone.get_default_timezone()
            )
            self.update_fingerprint_database()

    @staticmethod
    def get_featurizer(self, **kwargs):
        raise NotImplementedError(
            "make sure you add a custom 'get_featurizer' method. This should "
            "return a featurizer object to be used for generating fingerprints."
        )

    def get_fingerprint_distance(self, fingerprint1, fingerprint2) -> float:
        raise NotImplementedError(
            "If set the class attribute 'comparison_mode' to 'custom', make "
            "sure you add a custom 'get_fingerprint_distance' method. This should "
            "return a distance (float value) ."
        )

    @staticmethod
    def format_fingerprint(fingerprint):
        return fingerprint  # does nothing by default

    def check_structure(self, structure: Structure):

        # make the fingerprint for this structure and make into a numpy array for speed
        fingerprint1 = numpy.array(self.featurizer.featurize(structure))

        # apply any extra formatting
        fingerprint1 = self.format_fingerprint(fingerprint1)

        # We now want to get the distance of this fingerprint relative to all others.
        # If the distance is within the specified tolerance, then the structures
        # are too similar - and we return  for a failure.
        for fingerprint2 in self.fingerprint_database:

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
                # we can end the whole function as soon as one structure is
                # deemed too similar
                return False
            else:
                continue
        # If we make it through all structures and no distance is below the
        # tolerance, then we have a new and unique structure!

        # add this new structure to the database if it was requested.
        if self.add_unique_to_pool:
            self._add_fingerprint_to_database(fingerprint1)

        # Return that we were successful
        return True

    def update_fingerprint_database(self):

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

        # now grab all the new structures!
        new_structures = (
            self.structure_pool_queryset.filter(created_at__gte=last_update_safe)
            .only("structure")
            .to_toolkit()
        )

        # If there aren't any new structures, just exit without printing the
        # message and progress bar
        if not new_structures:
            return

        logging.info(
            f"Found {len(new_structures)} new structures for the fingerprint database."
        )

        # calculate each fingerprint and add it to the database
        for structure in track(new_structures):
            fingerprint = numpy.array(self.featurizer.featurize(structure))
            self._add_fingerprint_to_database(fingerprint)

    def _add_fingerprint_to_database(self, fingerprint):
        if self.fingerprint_database.size == 0:
            self.fingerprint_database = numpy.array([fingerprint])
        else:
            self.fingerprint_database = numpy.append(
                self.fingerprint_database, [fingerprint], axis=0
            )
