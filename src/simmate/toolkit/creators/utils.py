# -*- coding: utf-8 -*-

##############################################################################

from abc import ABC, abstractmethod


class FixIndicator(ABC):

    """
    This is an abstract base class for pointing to some class based on an
    input number of attempts. Note that these classes should be written to run
    in parallel and called accross multiple threads -- this means you should
    not store or update the attempt number within the class. Instead you must
    simply take the attempt number and return a class based on that number.
    """

    @abstractmethod
    def point_to_fix(self, attempt=0):
        raise NotImplementedError


##############################################################################


class SingleFix(FixIndicator):
    def __init__(self, fixes, cutoffs):

        # The object to ALWAYS point to for the fix
        self.fixes = fixes

        # The maximum number of times to try fixing
        self.cutoffs = cutoffs

    def point_to_fix(self, attempt=0):

        if attempt <= self.cutoffs:
            return self.fixes
        else:
            return False


##############################################################################


class SerialFixes(FixIndicator):
    def __init__(self, fixes, cutoffs):

        # How to handle the structure should check_structure() return false. Based on
        # the attempt number given in point_to_fix() and the maximum attempts allowed
        # for each fix (see maxFails), the point_to_fix() will return one of these objects.
        self.fixes = fixes

        # The maximum number of times that the respective gen/val object from onFail can be used
        # in a single sample creation. For example if check_structure keeps failing after 200
        # attempts of a given transformation, we may want to switch to a different
        # transfmoration method or new structure entirely.
        self.cutoffs = cutoffs

        # we need the cumulative maxFails list
        # for example, the maxFails=[20,40,10] needs to be converted to [20,60,70]
        # if infinite attempts are allowed, be sure to use float('inf') as the value
        # This list is more efficient to work with in the point_to_fix()
        #!!! should I make this numpy for speed below?
        self.cutoffs_cum = [sum(cutoffs[: x + 1]) for x in range(len(cutoffs))]

    def point_to_fix(self, attempt=0):

        # based on the attempt number and the maxFails list, see what stage of onFail we are on
        for i, attempt_cutoff in enumerate(self.cutoffs_cum):
            # if we are below the attempt cutoff, return the corresponding onFail object
            if attempt <= attempt_cutoff:
                return self.fixes[i]

        # If we make it through all of the cutoff list, that means we exceeded the maximum attempts allowed
        # In this case, we don't return return an object from the onFail list
        return False


##############################################################################


class NestedFixes(FixIndicator):
    def __init__(self, fixes, cutoffs):

        # How to handle the structure should check_structure() return false. Based on
        # the attempt number given in point_to_fix() and the maximum attempts allowed
        # for each fix (see maxFails), the point_to_fix() will return one of these objects.
        self.fixes = fixes

        # The maximum number of times that the respective gen/val object from onFail can be used
        # in a single sample creation. For example if check_structure keeps failing after 200
        # attempts of a given transformation, we may want to switch to a different
        # transfmoration method or new structure entirely.
        self.cutoffs = cutoffs

        # We need to know the fixing order, which is a bit trickier with nested fixes.
        # In nested, you will want to try the lowest order fix X number of times, then
        # try a higher order fix, then try the lowest order X number of times again.
        # For example, with a nest list of fixes=[new_lattice,new_sites] and
        # cutoffs=[3,5], you would start with a structure and try new_sites 5 times.
        # After these 5 failed attempts, you would then try a new_lattice. With this
        # new_lattice, you then try 5 new_sites again - the 5 new fail attempts would
        # trigger another new_lattice. Once new_lattice has be done 3 times without
        # any success, we say the validator has ran out of attempts.
        # To do this, I make a list of all the the attempts. The list is the length
        # of the total number of attempts and each entry points to the index of fixes
        # that should be used.
        #!!! the size of this list is an issue if many attempts are allowed
        #!!! for example cutoffs=[100,100,100] would make a list of length 1,010,100
        #!!! For validators where I want thousands of nested attempts, this could cause a memory issue.
        #!!! Should I warn the user if this is too large?
        # grab the total number of attempts allowed accross all portions
        self.max_attempt = get_nested_size(cutoffs)
        # grab the map which will be a list of length max_attempt
        self.attempt_map = get_nested_map(cutoffs)

        # the above code works, but I want to remove the starting upper-level fixes
        # In the [new_lattice,new_sites] example, I want to make sure we start with new_sites
        self.max_attempt = self.max_attempt - len(cutoffs) + 1
        self.attempt_map = self.attempt_map[len(cutoffs) - 1 :]

    def point_to_fix(self, attempt=0):

        if attempt >= self.max_attempt:
            return False
        # we have a nest map here, so we can just access it
        return self.fixes[self.attempt_map[attempt - 1]]  # -1 for index counting from 0


#!!! should I make the two functions below @staticmethods of the above class?
def get_nested_map(a):
    l = []
    for i in range(len(a) - 1, -1, -1):
        l = a[i] * ([i] + l)
    return l


def get_nested_size(a):
    if len(a) == 1:
        size = a[0]
    else:
        nest = get_nested_size(a[1:])
        size = a[0] * nest + a[0]
    return size


##############################################################################
