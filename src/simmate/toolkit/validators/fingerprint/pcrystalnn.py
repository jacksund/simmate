# -*- coding: utf-8 -*-

import numpy

from tqdm import tqdm

from matminer.featurizers.site import CrystalNNFingerprint

from simmate.toolkit.featurizers.fingerprint import PartialsSiteStatsFingerprint

# TODO: what if we want to add to the initial_structures list later on? Should this
# be integrated with the Simmate database tables? An example use-case is with 
# evolutionary searches where structures can be added at random times, but those
# additions won't be reflected here...
# One potential solution is to have an "update_fingerprint_table" method along with
# structure_ids list. We'd make this so initial_structures can be either a
# list of structures OR a structure database table.

class PartialCrystalNNFingerprint:
    def __init__(
        self,
        composition,
        stat_options=["mean", "std_dev", "minimum", "maximum"],
        initial_structures=[],
        **crystalnn_options,
    ):

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
        self.featurizer = PartialsSiteStatsFingerprint(
            sitefingerprint_method, stats=stat_options
        )

        # for this specific featurizer, you're supposed to use the .fit() function
        # with an example structure but really, all that does is get a list of
        # unique elements - so we can make that with a composition object
        self.featurizer.elements_ = numpy.array(
            [element.symbol for element in composition.elements]
        )

        # Generate the fingerprint for each of the initial input structures
        # We convert this to a numpy array for speed improvement at later stages
        # OPTIMIZE: this can be slow and I should support parallel featurization
        self.fingerprint_database = numpy.array(
            [
                self.featurizer.featurize(structure)
                for structure in tqdm(initial_structures)
            ]
        )

    def check_structure(self, structure, tolerance=1e-4):

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

        # add this new structure to the database
        if self.fingerprint_database.size == 0:
            self.fingerprint_database = numpy.array([fingerprint1])
        else:
            self.fingerprint_database = numpy.append(
                self.fingerprint_database, [fingerprint1], axis=0
            )

        # Return that we were successful
        return True
