# -*- coding: utf-8 -*-

import numpy
from tqdm import tqdm

from django.utils import timezone

# BUG: This prints a tqdm error so we silence it here.
import warnings

with warnings.catch_warnings(record=True):
    from matminer.featurizers.site import CrystalNNFingerprint

# BUG: waiting on this pSS to be added to matminer. See the following PR:
#   https://github.com/hackingmaterials/matminer/pull/809
from matminer.featurizers.structure.sites import (
    SiteStatsFingerprint,
)  # PartialsSiteStatsFingerprint


class PartialCrystalNNFingerprint:
    def __init__(
        self,
        composition,
        stat_options=["mean", "std_dev", "minimum", "maximum"],
        structure_pool=[],  # either a list of structures OR a queryset
        add_unique_to_pool=True,  # whether to add fingerprint when check_structure is true
        **crystalnn_options,
    ):

        self.add_unique_to_pool = add_unique_to_pool

        # make the matminer featurizer object using the provided settings
        if crystalnn_options:
            sitefingerprint_method = CrystalNNFingerprint(**crystalnn_options)
        # if no settings were given, we will use those from the Materials Project
        #   https://docs.materialsproject.org/user-guide/structure-similarity/
        else:
            # We change x_diff_weight to 3 here because we want the coordation
            # to be atom-dependent (best we can do is oxidation-state dependent here)
            sitefingerprint_method = CrystalNNFingerprint.from_preset(
                "ops", distance_cutoffs=None, x_diff_weight=3
            )

        # now that we made the sitefingerprint_method, we can input it into the
        # structurefingerprint_method which finishes up the featurizer
        self.featurizer = SiteStatsFingerprint(
            sitefingerprint_method, stats=stat_options
        )

        # for this specific featurizer, you're supposed to use the .fit() function
        # with an example structure but really, all that does is get a list of
        # unique elements - so we can make that with a composition object
        self.featurizer.elements_ = numpy.array(
            [element.symbol for element in composition.elements]
        )

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
                    for structure in tqdm(structure_pool)
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

    def check_structure(self, structure, tolerance=0.001):
        # OPTIMIZE: my choice of tolerance is based on my evolutionary search.
        # However, "clustering" after evolutionary search suggests that something
        # like 0.5 might be a better choice for finding a truly unique structure

        # make the fingerprint for this structure and make into a numpy array for speed
        fingerprint1 = numpy.array(self.featurizer.featurize(structure))

        # We now want to get the distance of this fingerprint relative to all others.
        # If the distance is within the specified tolerance, then the structures
        # are too similar - and we return  for a failure.
        for fingerprint2 in self.fingerprint_database:
            distance = numpy.linalg.norm(fingerprint1 - fingerprint2)
            if distance < tolerance:
                # we can end the whole function as soon as one structure is deemed too similar
                return False
            else:
                continue
        # If we make it through all structures and no distance is below the
        # tolerance, we have a new and unique structure!

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

        # BUG: what if a structure was added to the table WHILE I was running the
        # last query? This sets up a race condition with new structures and my
        # last_update timestamp. To avoid this bug, I immediately update our
        # timestamp, rather than doing it after the query
        last_update_safe = self.last_update
        self.last_update = timezone.now()

        # now grab all the new structures!
        new_structures = (
            self.structure_pool_queryset.filter(created_at__gte=last_update_safe)
            .only("structure_string")
            .to_toolkit()
        )

        # If there aren't any new structures, just exit without printing the
        # message and tqdm progress bar below
        if not new_structures:
            return

        print(
            f"Found {len(new_structures)} new structures for the fingerprint database."
        )

        # calculate each fingerprint and add it to the database
        for structure in tqdm(new_structures):
            fingerprint = numpy.array(self.featurizer.featurize(structure))
            self._add_fingerprint_to_database(fingerprint)

    def _add_fingerprint_to_database(self, fingerprint):
        if self.fingerprint_database.size == 0:
            self.fingerprint_database = numpy.array([fingerprint])
        else:
            self.fingerprint_database = numpy.append(
                self.fingerprint_database, [fingerprint], axis=0
            )
