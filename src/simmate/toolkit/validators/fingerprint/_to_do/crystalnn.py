# -*- coding: utf-8 -*-

import numpy as np

from matminer.featurizers.site import CrystalNNFingerprint as cnnf

#!!! is it faster to import these all at once?
from matminer.featurizers.structure import SiteStatsFingerprint as ssf
from matminer.featurizers.structure import RadialDistributionFunction as rdf
from matminer.featurizers.structure import PartialRadialDistributionFunction as prdf


class CrystalNNFingerprint:

    # requires matminer code
    # see https://materialsproject.org/docs/structuresimilarity

    def __init__(
        self,
        on_fail,
        max_fails,
        cnn_options={},
        stat_options=["mean", "std_dev", "minimum", "maximum"],
        initial_structures=[],
        parallel=False,
    ):

        self.on_fail = on_fail

        # we need the cumulative max_fails list
        # for example, the max_fails=[20,40,10] needs to be converted to [20,60,70]
        # if infinite attempts are allowed, be sure to use float('inf') as the value
        # This list is more efficient to work with in the point_next_step()
        #!!! should I make this numpy for speed below?
        self.max_fails_cum = [sum(max_fails[: x + 1]) for x in range(len(max_fails))]

        # make the matminer featurizer object
        # if it isnt set, we will use the default, which is set to what the Materials project uses
        if cnn_options:
            sitefingerprint_method = cnnf(**cnn_options)
        else:
            # see https://materialsproject.org/docs/structuresimilarity
            sitefingerprint_method = cnnf.from_preset(
                "ops", distance_cutoffs=None, x_diff_weight=0
            )
        # now that we made the sitefingerprint_method, we can input it into the structurefingerprint_method which finishes up the featurizer
        self.featurizer = ssf(sitefingerprint_method, stats=stat_options)

        # generate the fingerprint for each of the initial input structures
        # note this uses the parallel method for the matminer featurizer
        # if there are less the 15 structures, parallel method is actually slower than serial
        # so we check that first and decide which is quickest
        # sometimes the script will stall/fail when trying parallel (like when in Spyder) so the option to turn of parallel is also there
        if len(initial_structures) <= 15 and not parallel:
            # do this serially and make into a numpy array for speed
            self.fingerprint_database = np.array(
                [
                    self.featurizer.featurize(structure)
                    for structure in initial_structures
                ]
            )
        else:
            # use matminer's parallel functionality and make into a numpy array for speed
            self.fingerprint_database = self.featurizer.featurize_many(
                initial_structures, pbar=False
            )

    def check_structure(self, structure, tolerance=1e-4):

        # make the fingerprint for this structure and make into a numpy array for speed
        fingerprint1 = np.array(self.featurizer.featurize(structure))

        # we now want to get the distance of this fingerprint relative to all others
        # if the distance is within the specified tolerance, then the structures are too similar - we return false
        # if we make it through all structures and no distance is below the tolerance, we are good to go!
        for fingerprint2 in self.fingerprint_database:
            distance = np.linalg.norm(fingerprint1 - fingerprint2)
            if distance < tolerance:
                # we can end the whole function as soon as one structure is deemed too similar
                return False
            else:
                continue

        # if we finished the loop above, we can add this structure to the database and return a success
        # this method I use to append is pretty slow for numpy. Is there a better way to do this?
        if self.fingerprint_database.size == 0:
            self.fingerprint_database = np.array([fingerprint1])
        else:
            self.fingerprint_database = np.append(
                self.fingerprint_database, [fingerprint1], axis=0
            )

        return True
