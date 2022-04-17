# -*- coding: utf-8 -*-

import numpy as np

from matminer.featurizers.site import CrystalNNFingerprint as cnnf

#!!! is it faster to import these all at once?
from matminer.featurizers.structure import SiteStatsFingerprint as ssf
from matminer.featurizers.structure import RadialDistributionFunction as rdf
from matminer.featurizers.structure import PartialRadialDistributionFunction as prdf
from matminer.featurizers.structure.sites import PartialsSiteStatsFingerprint

from scipy.spatial.distance import cosine


class ASEFingerprint:

    # ASE cites this as a rewrite of the USPEX fingerprint
    # https://gitlab.com/ase/ase/-/blob/master/ase/ga/ofp_comparator.py

    def __init__(self, composition, on_fail, max_fails, initial_structures=[]):

        self.on_fail = on_fail

        # we need the cumulative max_fails list
        # for example, the max_fails=[20,40,10] needs to be converted to [20,60,70]
        # if infinite attempts are allowed, be sure to use float('inf') as the value
        # This list is more efficient to work with in the point_next_step()
        #!!! should I make this numpy for speed below?
        self.max_fails_cum = [sum(max_fails[: x + 1]) for x in range(len(max_fails))]

        # we can assume the user has ASE installed because it is a dependency of PyMatgen
        #!!! it looks like the ase.ga module is actively changing so version may introduce errors
        from ase.ga.ofp_comparator import OFPComparator

        self.featurizer = OFPComparator(  # n_top=None, # atoms to optimize. None is all of them
            # dE=1.0, # energy difference to be considered different (not used here b/c we dont have a calculator)
            # cos_dist_max=5e-3, # cosine distance for structure to be considered different
            # rcut=20., # cutoff radius for the fingerprint
            # binwidth=0.05, # bin width (in Angstrom) over which fingerprints are discretized
            # sigma=0.02, # smearing of the guassian in fingerprint
            # nsigma=4, # distance where smearing is cut off
            # pbc=True, # whether to apply periodic boundry conditions
            # maxdims=None, # not used if we have a 3d crystal
            # recalculate=False # wether to recalculate fingerprints in ASE database
        )

        # we also need to convert pymatgen Structures to ase Atoms below
        #!!! is it faster and more memory efficient to import below?
        from pymatgen.io.ase import AseAtomsAdaptor

        self.adaptor = AseAtomsAdaptor

        # generate the fingerprint for each of the initial input structures
        self.fingerprint_database = []
        for structure in initial_structures:
            # convert the structure to ase Atoms object
            structure_ase = self.adaptor.get_atoms(structure)

            # make the fingerprint
            # ase uses .looks_like() to compare two structures, but we want the lower-level function ._take_fingerprints()
            output = self.featurizer._take_fingerprints(structure_ase)
            # the output is a tuple of...
            # (1) dictionary with keys of each element combo mapped to the fingerprint
            # (2) dictionary with keys of element to the indicies of that element in the Atoms object
            # so I want to make the fingerprint a 1D array so I go through the output and merge these.
            # make a list of each element-element fingerprint
            fingerprints = [output[0][key] for key in output[0]]
            # now combine the fingerprints into a single 1D array
            fingerprint = np.hstack(fingerprints)

            # add to the database
            self.fingerprint_database.append(fingerprint)
        # now make the datebase into a numpy array for speed
        self.fingerprint_database = np.array(self.fingerprint_database)

    def check_structure(self, structure, tolerance=5e-3):

        # convert the structure to ase Atoms object
        structure_ase = self.adaptor.get_atoms(structure)

        # make the fingerprint
        # ase uses .looks_like() to compare two structures, but we want the lower-level function ._take_fingerprints()
        output = self.featurizer._take_fingerprints(structure_ase)
        # the output is a tuple of...
        # (1) dictionary with keys of each element combo mapped to the fingerprint
        # (2) dictionary with keys of element to the indicies of that element in the Atoms object
        # so I want to make the fingerprint a 1D array so I go through the output and merge these.
        # make a list of each element-element fingerprint
        fingerprints = [output[0][key] for key in output[0]]
        # now combine the fingerprints into a single 1D array
        fingerprint1 = np.hstack(fingerprints)

        # we now want to get the distance of this fingerprint relative to all others
        # if the distance is within the specified tolerance, then the structures are too similar - we return false
        # if we make it through all structures and no distance is below the tolerance, we are good to go!
        for fingerprint2 in self.fingerprint_database:
            # we want the cosine distance
            # https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.distance.cosine.html
            # I use the numpy version of this for speed
            distance = cosine(fingerprint1, fingerprint2)
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

    def point_next_step(self, attempt=0):

        # based on the attempt number and the max_fails list, see what stage of on_fail we are on
        for i, attempt_cutoff in enumerate(self.max_fails_cum):
            # if we are below the attempt cutoff, return the corresponding on_fail object
            if attempt <= attempt_cutoff:
                return self.on_fail[i]

        # If we make it through all of the cutoff list, that means we exceeded the maximum attempts allowed
        # In this case, we don't return return an object from the on_fail list
        return False
