# -*- coding: utf-8 -*-

"""
This code will likely move or be condensed in future versions. If you'd like to
write your own fingerprint validator, simply follow the format shown in the 
base.py validator script.
"""

#!!! I should consider other 'distance' operations
# from scipy.spatial.distance --- https://docs.scipy.org/doc/scipy-0.14.0/reference/spatial.distance.html

#!!! Also note that the scipy versions are slower because they perform checks before doing the calculation
#!!! to avoid this, look at the source code for each scipy call and you'll see what the numpy code should be
# Here's an example showing how scipy's call for scipy.spatial.distance.euclidean (which calls scipy.linalg.norm) is much slower than numpy
# from scipy.linalg import norm as normsp
# from numpy.linalg import norm as normnp
# import numpy as np
# a = np.random.random(size=(1000, 2000))
# %timeit normsp(a)
# %timeit normnp(a)

##############################################################################

import numpy as np

from matminer.featurizers.site import CrystalNNFingerprint as cnnf

#!!! is it faster to import these all at once?
from matminer.featurizers.structure import SiteStatsFingerprint as ssf
from matminer.featurizers.structure import RadialDistributionFunction as rdf
from matminer.featurizers.structure import PartialRadialDistributionFunction as prdf

##############################################################################


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

    def point_next_step(self, attempt=0):

        # based on the attempt number and the max_fails list, see what stage of on_fail we are on
        for i, attempt_cutoff in enumerate(self.max_fails_cum):
            # if we are below the attempt cutoff, return the corresponding on_fail object
            if attempt <= attempt_cutoff:
                return self.on_fail[i]

        # If we make it through all of the cutoff list, that means we exceeded the maximum attempts allowed
        # In this case, we don't return return an object from the on_fail list
        return False


##############################################################################

#!!! CHANGE TO COS DISTANCE
class RDFFingerprint:

    # requires matminer code
    # see https://materialsproject.org/docs/structuresimilarity

    def __init__(
        self,
        on_fail,
        max_fails,
        cutoff=20.0,
        bin_size=0.1,  #!! consider changing to kwargs
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
        self.featurizer = rdf(cutoff, bin_size)

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
        # the [0]['distribution'] reformats the output to an actual fingerprint (1D numpy array) that we want
        fingerprint1 = np.array(self.featurizer.featurize(structure)[0]["distribution"])

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

    def point_next_step(self, attempt=0):

        # based on the attempt number and the max_fails list, see what stage of on_fail we are on
        for i, attempt_cutoff in enumerate(self.max_fails_cum):
            # if we are below the attempt cutoff, return the corresponding on_fail object
            if attempt <= attempt_cutoff:
                return self.on_fail[i]

        # If we make it through all of the cutoff list, that means we exceeded the maximum attempts allowed
        # In this case, we don't return return an object from the on_fail list
        return False


##############################################################################

#!!! CHANGE TO COS DISTANCE
class PartialRDFFingerprint:

    # requires matminer code
    # see https://materialsproject.org/docs/structuresimilarity

    def __init__(
        self,
        composition,
        on_fail,
        max_fails,
        cutoff=20.0,
        bin_size=0.1,  #!! consider changing to kwargs
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
        self.featurizer = prdf(cutoff, bin_size)

        # for this specific featurizer, you're supposed to use the .fit() function with an example structure
        # but really, all that does is get a list of unique elements - so we can make that with a composition object
        #!!! note - if there are ever issues in the code, I would look here first!
        self.featurizer.elements_ = np.array(
            [element.symbol for element in composition.elements]
        )

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

        # the .featurize() returns a 1D array without the corresponding x values
        # for a more human-readable output, use .compute_prdf(structure), which is actually used insides of .featurize()
        # dist_bins, prdf = prdf1.compute_prdf(rocksalt)  # assembles the PRDF for each pair

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

    def point_next_step(self, attempt=0):

        # based on the attempt number and the max_fails list, see what stage of on_fail we are on
        for i, attempt_cutoff in enumerate(self.max_fails_cum):
            # if we are below the attempt cutoff, return the corresponding on_fail object
            if attempt <= attempt_cutoff:
                return self.on_fail[i]

        # If we make it through all of the cutoff list, that means we exceeded the maximum attempts allowed
        # In this case, we don't return return an object from the on_fail list
        return False


##############################################################################

from pymatdisc.core.featurizers.fingerprint import PartialsSiteStatsFingerprint


class PartialCrystalNNFingerprint:

    # requires matminer code
    # see https://materialsproject.org/docs/structuresimilarity

    def __init__(
        self,
        composition,
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
            # We change x_diff_weight to 3 here because we want the coordation to be atom dependent (best we can do is oxidation-state dependent here)
            sitefingerprint_method = cnnf.from_preset(
                "ops", distance_cutoffs=None, x_diff_weight=3
            )
        # now that we made the sitefingerprint_method, we can input it into the structurefingerprint_method which finishes up the featurizer
        #!!! will need to import this from matminer when it is moved there
        self.featurizer = PartialsSiteStatsFingerprint(
            sitefingerprint_method, stats=stat_options
        )

        # for this specific featurizer, you're supposed to use the .fit() function with an example structure
        # but really, all that does is get a list of unique elements - so we can make that with a composition object
        #!!! note - if there are ever issues in the code, I would look here first!
        self.featurizer.elements_ = np.array(
            [element.symbol for element in composition.elements]
        )

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

    def point_next_step(self, attempt=0):

        # based on the attempt number and the max_fails list, see what stage of on_fail we are on
        for i, attempt_cutoff in enumerate(self.max_fails_cum):
            # if we are below the attempt cutoff, return the corresponding on_fail object
            if attempt <= attempt_cutoff:
                return self.on_fail[i]

        # If we make it through all of the cutoff list, that means we exceeded the maximum attempts allowed
        # In this case, we don't return return an object from the on_fail list
        return False


##############################################################################

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


##############################################################################


### THIS CODE IS FOR TIME TESTING ###

# from pymatgen import MPRester

# mpr = MPRester('2Tg7uUvaTAPHJQXl')

# # Get structures. I import a bunch of test cases, but I'll do the testing with perovskite.
# diamond = mpr.get_structure_by_material_id("mp-66")
# gaas = mpr.get_structure_by_material_id("mp-2534")
# rocksalt = mpr.get_structure_by_material_id("mp-22862")
# perovskite = mpr.get_structure_by_material_id("mp-5827")
# spinel_caco2s4 = mpr.get_structure_by_material_id("mvc-12728")
# spinel_sicd2O4 = mpr.get_structure_by_material_id("mp-560842")

# test = ASEFingerprint(perovskite.composition,
#                       on_fail=[],
#                       max_fails=[],
#                       initial_structures=[])

# print(test.check_structure(perovskite))

# ##############################################################################

# import time
# from tqdm import tqdm

# # I will record structure sizes and times into lists
# num_sites = []
# cnnf_times = []
# rdff_times = []
# prdff_times = []
# pcnnf_times = []

# # start with a [1,1,1] cell size
# size = [0,1,1] # because we start adding below - I have the first at 0, the first cycle will turn this into a 1

# # we are going to try 10 different supercell sizes
# for n in tqdm(range(10)):

#     # reset the perovskite structure to its unitcell
#     perovskite = mpr.get_structure_by_material_id("mp-5827")

#     # change the supercell size
#     # this line will make sizes increment by one in each axis (111, 211, 221, 222, 322, 332, ...)
#     size[n % 3] += 1

#     # use the size to make the pervoskite supercell
#     perovskite.make_supercell(size)

#     # append the cell size
#     num_sites.append(perovskite.num_sites)


#     ##### TEST METHOD 1 #####
#     fpval = CrystalNNFingerprint(on_fail=[], max_fails=[],
#                                 cnn_options={}, stat_options=['mean', 'std_dev', 'minimum', 'maximum'],
#                                 initial_structures=[], parallel=False)

#     s = time.time()
#     check1 = fpval.check_structure(perovskite)
#     # check2 = fpval.check_structure(perovskite)
#     e = time.time()
#     cnnf_times.append(e-s)
#     #########################

#     ##### TEST METHOD 2 #####
#     fpval2 = RDFFingerprint(on_fail=[], max_fails=[])

#     s = time.time()
#     check01 = fpval2.check_structure(perovskite)
#     # check02 = fpval2.check_structure(perovskite)
#     e = time.time()
#     rdff_times.append(e-s)
#     #########################

#     ##### TEST METHOD 3 #####
#     fpval3 = PartialRDFFingerprint(composition=perovskite.composition, on_fail=[], max_fails=[])

#     s = time.time()
#     check001 = fpval3.check_structure(perovskite)
#     # check002 = fpval3.check_structure(perovskite)
#     e = time.time()
#     prdff_times.append(e-s)
#     #########################

#     ##### TEST METHOD 4 #####
#     fpval4 = PartialCrystalNNFingerprint(composition=perovskite.composition,
#                                           on_fail=[], max_fails=[],
#                                           cnn_options={}, stat_options=['mean', 'std_dev', 'minimum', 'maximum'],
#                                           initial_structures=[], parallel=False)

#     s = time.time()
#     check0001 = fpval4.check_structure(perovskite)
#     # check0002 = fpval4.check_structure(perovskite)
#     e = time.time()
#     pcnnf_times.append(e-s)
#     #########################


# # Now let's plot the results

# ### IMPORT PLOTLY FUNCTIONS ###
# import plotly.graph_objects as go
# from plotly.offline import plot

# series1 = go.Scatter(name='CrystalNNFingerprint',
#                      x=num_sites,
#                      y=cnnf_times,
#                      mode='lines+markers',
#                     )

# series2 = go.Scatter(name='RDFFingerprint',
#                      x=num_sites,
#                      y=rdff_times,
#                      mode='lines+markers',
#                     )

# series3 = go.Scatter(name='PartialRDFFingerprint',
#                      x=num_sites,
#                      y=prdff_times,
#                      mode='lines+markers',
#                     )

# series4 = go.Scatter(name='PartialCrystalNNFingerprint',
#                      x=num_sites,
#                      y=pcnnf_times,
#                      mode='lines+markers',
#                     )

# layout = go.Layout(width=800,
#                    height=600,
#                    plot_bgcolor='white',
#                    paper_bgcolor='white',
#                    xaxis=dict(title_text='Cell Size (# sites)',
#                               #range=[2,5.2],
#                               showgrid=False,
#                               zeroline=False,
#                               ticks='outside',
#                               tickwidth=2,
#                               showline=True,
#                               color='black',
#                               linecolor='black',
#                               linewidth=2,
#                               mirror=True,
#                               #dtick=0.5,
#                               #tick0=1.75,
#                               ),
#                    yaxis=dict(title_text='Fingerprint Time (s)',
#                               #range=[-0.25,10],
#                               showgrid=False,
#                               zeroline=False,
#                               ticks='outside',
#                               tickwidth=2,
#                               showline=True,
#                               linewidth=2,
#                               color='black',
#                               linecolor='black',
#                               mirror=True,
#                               #dtick=2,
#                               #tick0=0,
#                               ),
#                    legend=dict(x=0.05,
#                                y=0.95,
#                                bordercolor='black',
#                                borderwidth=1,
#                                font=dict(color='black'),
#                                ),
#                    )

# fig = go.Figure(data=[series1,series2,series3,series4],
#                 layout=layout)

# plot(fig, config={'scrollZoom': True})

##############################################################################
