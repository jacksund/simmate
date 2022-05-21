# -*- coding: utf-8 -*-

from typing import Callable

from simmate.calculators.vasp.inputs.incar_modifiers import (
    keyword_modifier_density,
    keyword_modifier_density_a,
    keyword_modifier_density_b,
    keyword_modifier_density_c,
    keyword_modifier_per_atom,
    keyword_modifier_smart_magmom,
    keyword_modifier_smart_lmaxmix,
    keyword_modifier_smart_ldau,
    keyword_modifier_smart_ismear,
)


class Incar(dict):
    """
    INCAR object for reading and writing INCAR files. This behaves exactly like
    a python dictionary, but has a few extra checks and methods attached to it.
    You can pass it a dictionary or initialize it just like you would dict(kwargs).
    You can consider the dict(kwargs) as equivalent to Incar(parameters).

    If you want a given setting to be dependent on the structure or dynamically
    determined, then we implement these modifiers. This would enable us to
    do things like ENCUT__per_atom or NGZF__density. We can even have more complex
    modifiers like multiple_keywords__smart_ldau which signals that our
    "smart_ldau" modifier introduces more than one new setting to the INCAR, such
    as LDAUJ, LDAUU, LDAUL, LDAUTYPE, and LDAUPRINT.
    """

    def __init__(self, **kwargs):

        # The kwargs are a dictionary of parameters (e.g. {"PREC": "accurate"})

        # Establish the dictionary with the given input
        # This is the same as doing dict(**kwargs)
        super().__init__(**kwargs)

        # Based on the kwargs, go through and make sure each parameter is in
        # it's expected datatype. Thus users can supply strings in the typical
        # VASP format that will be convert to python types here.
        # OPTIMIZE -- would it be faster if I only did this on from_file init?
        # and therefore assumed the user to initialize this with proper python
        # datatypes and formatting? Also will this behave properly if the value
        # is already in the correct format?
        for parameter, value in self.items():

            # parameters may have tags like "__density" added onto them. We don't
            # convert to the datatype yet, but instead wait until a structure
            # is provided (when the to_file or str methods are called below).
            # These are defined in python and should already be in the correct
            # data format.
            if "__" in parameter:
                self.update({parameter: value})

            # Otherwise, we need to convert values to the proper python datatype
            # because we might be reading from a file where everything is a string
            else:
                formatted_value = self._str_to_datatype(parameter, value)
                self.update({parameter: formatted_value})

        # SPECIAL CASE
        # If you have LSORBIT=True or LNONCOLLINEAR=True, the MAGMOM class needs
        # to take on a different form. Instead of a single MAGMOM being set as
        # a float, it's now a vector (x,y,z). For example:
        #   MAGMOM = x1 y1 z1    x2 y2 z2    x3 y3 z3 ...
        #       [...instead of...]
        #   MAGMOM = value1 value2 value3 ...
        # Check if MAGMOM is set along with LSORBIT or LNONCOLLINEAR being True
        if ("MAGMOM" in kwargs) and (
            kwargs.get("LSORBIT") or kwargs.get("LNONCOLLINEAR")
        ):
            # convert the MAGMOM value from...
            #   [x1,y1,z1,x2,y2,z2,x3,y3,z3] (this can be a string too)
            #   to...
            #   [[x1,y1,z1],[x2,y2,z2],[x3,y3,z3]]
            old_format = kwargs["MAGMOM"]
            new_format = [old_format[i : i + 3] for i in range(0, len(old_format), 3)]
            # Or If I wanted to do the same thing with numpy:
            #   new_format = numpy.array_split(old_format, len(old_format) // 3)
            # now update the dictionary with this value
            self.update({"MAGMOM": new_format})

    def to_evaluated_str(self, structure=None):

        # Let's start with an empty string and build from there
        final_str = ""

        # First we need to iterate through all parameters and check if we have
        # ones that are structure-specific. For example, we would need to
        # evaluate "ENCUT__per_atom". We go through all these and collect the
        # parameters into a final settings list.
        final_settings = {}
        for parameter, value in self.items():

            # if there is no modifier attached to the parameter, we just keep it as-is
            if "__" not in parameter:
                final_settings[parameter] = value

            # Otherwise we have a modifier like "__density" and need to evaluate it
            else:

                # make sure we have a structure supplied because all modifiers
                # require one.
                if not structure:
                    raise Exception(
                        "It looks like you used a keyword modifier but didn't "
                        f"supply a structure! If you want to use {parameter}, "
                        "then you need to make sure you provide a structure so "
                        "that the modifier can be evaluated."
                    )

                # separate the input into the base parameter and modifier.
                # This also overwrites what our paramter value is.
                parameter, modifier_tag = parameter.split("__")

                # check that this class has this modifier supported. It should
                # be a method named "keyword_modifier_mymodifier".
                # If everything looks good, we grab the modifier function
                modifier_fxn_name = "keyword_modifier_" + modifier_tag
                if hasattr(self, modifier_fxn_name):
                    modifier_fxn = getattr(self, modifier_fxn_name)
                else:
                    raise AttributeError(
                        """
                        It looks like you used a keyword modifier that hasn't
                        been defined yet! If you want something like ENCUT__smart_encut,
                        then you need to make sure there is a keyword_modifier_smart_encut
                        method available.
                        """
                    )

                # now that we have the modifier function, let's use it to update
                # our value for this keyword.
                value = modifier_fxn(structure, value)

                # sometimes the modifier returns None. In this case we don't
                # set anything in the INCAR, but leave it to the programs
                # default value.
                if not value:
                    continue
                # BUG: Are there cases where None is return but we still want
                # to write it to the INCAR? If so, it'd be skipped here.

                # if the "parameter" is actually "multiple_keywords", then we
                # have our actual parameters as a dictionary. We need to
                # pull these out of the "value" we have.
                if parameter == "multiple_keywords":
                    for subparameter, subvalue in value.items():
                        final_settings[subparameter] = subvalue

                # otherwise we were just given back an update value
                else:
                    final_settings[parameter] = value

        # Now that we have all of our parameters evaluated for the structure, we
        # iterate through each parameter and its set value. Each one will be
        # put on a separate line.
        for parameter, value in final_settings.items():

            # let's start by adding the parameter key to our output
            # It will be followed by an equal sign to separate it's value
            final_str += parameter + " = "

            # If we have a value that is a list (or list of lists)
            if isinstance(value, list):

                # check if we have a list of lists
                # Take MAGMOM with LSORBIT=True as an example, where we convert...
                #   [[x1,y1,z1],[x2,y2,z2],[x3,y3,z3]]
                # to...
                # "x1 y1 z1 x2 y2 z2 x3 y3 z3"
                if isinstance(value[0], list):
                    final_str += " ".join(str(n) for xyz in value for n in xyz)

                # otherwise we just have a list of items
                # converts [1, 2, 3] to "1 2 3"
                else:
                    final_str += " ".join(str(n) for n in value)

            # if it's not a list, we can just save the string of the value
            else:
                final_str += str(value)

            # we want to start each parameter on a new line, so we need to
            # add this at the end of each. There will be an extra new line at
            # the end of the file, but that's alright
            final_str += "\n"

        # we now have our final string and can return it!
        return final_str

    def to_file(self, filename="INCAR", structure=None):
        """
        Write Incar to a file.
        Args:
            filename (str): filename to write to.
        """
        # we just take the string format and put it in a file
        with open(filename, "w") as file:
            file.write(self.to_evaluated_str(structure=structure))

    @staticmethod
    def from_file(filename="INCAR"):
        """
        Reads an Incar object from a file.
        Args:
            filename (str): Filename for file
        Returns:
            Incar object
        """
        # open the file, grab the lines, and then close it
        with open(filename) as file:
            lines = file.readlines()

        # store parameters in this dictionary
        parameters = {}
        # go through line by line
        for line in lines:
            # If the line starts with a # then its a comment and we should skip.
            # It also could be an empty line that we should skip,
            if line.startswith("#") or line.startswith("\n"):
                continue
            # multiple parameters on a single line are separated by a semicolon
            for sub_line in line.split(";"):
                # the PARAMETER and VALUE are separated by equal sign
                parameter, value = sub_line.split("=")
                # we can use the parameter/value to update our dictionary. The
                # last thing we do is remove leading/trailing whitespace with strip()
                parameters[parameter.strip()] = value.strip()

        # return the final dictionary as an Incar object
        return Incar(**parameters)

    @staticmethod
    def _str_to_datatype(parameter, value):
        """
        When given a vasp parameter and it's value as a string, this helper
        function will use the key (parameter) to determine how to convert the
        val string to the proper python datatype (int, float, bool, list...).
        I have the most common keys mapped out, but if a parameter is given that
        isn't mapped, I simply leave it as a string.
        """

        # I outline the most common keys to what their expected data types are.

        # OPTIMIZE -- I should set these elsewhere so that these lists are not
        # initialized every time I call this function. Maybe have a dictionary
        # of {Parameter: Value_datatype} in the main enviornment for use.

        vector_list_keys = (
            # "MAGMOM",  # depends on other args -- see notes in init
            "DIPOL",
        )

        float_list_keys = (
            "LDAUU",
            "LDAUJ",
            "MAGMOM",  # depends on other args -- see notes in init
            "LANGEVIN_GAMMA",
            "QUAD_EFG",
            "EINT",
        )
        int_list_keys = (
            "LDAUL",
            "LDAUJ",
            "EINT",
        )

        bool_keys = (
            "LDAU",
            "LWAVE",
            "LSCALU",
            "LCHARG",
            "LPLANE",
            "LUSE_VDW",
            "LHFCALC",
            "ADDGRID",
            "LSORBIT",
            "LNONCOLLINEAR",
            "KGAMMA",
        )
        float_keys = (
            "EDIFF",
            "SIGMA",
            "TIME",
            "ENCUTFOCK",
            "HFSCREEN",
            "POTIM",
            "EDIFFG",
            "AGGAC",
            "PARAM1",
            "PARAM2",
            "KSPACING",
            "SYMPREC",
            "AMIX",
            "BMIX",
            "AMIN",
            "SMASS",
            "AMIX_MAG",
            "BMIX_MAG",
        )
        int_keys = (
            "NSW",
            "NBANDS",
            "NELMIN",
            "ISIF",
            "IBRION",
            "ISPIN",
            "ICHARG",
            "NELM",
            "ISMEAR",
            "NPAR",
            "LDAUPRINT",
            "LMAXMIX",
            "ENCUT",
            "NSIM",
            "NKRED",
            "NUPDOWN",
            "ISPIND",
            "LDAUTYPE",
            "IVDW",
            "ISTART",
            "NELMDL",
            "IMIX",
            "ISYM",
        )

        # If the value is not a string, then assume we are already in the
        # correct format. Note, an incorrect format will throw an error
        # somewhere below, which may be tricky for beginners to traceback.
        if not isinstance(value, str):
            return value

        # if the parameter is in int_keys
        if parameter in int_keys:
            # sometimes "1." was written to indicate an integer so check for
            # this and remove it if needed.
            if value[-1] == ".":
                value = value[:-1]
            # return the value integer
            return int(value)

        # if the parameter is in float_keys, we convert value to a float
        elif parameter in float_keys:
            # return the value float
            return float(value)

        # if the parameter is in bool_keys
        elif parameter in bool_keys:
            # Python is weird where bool("FALSE") will return True... So I need
            # to convert the string to lowercase and read it to know what to
            # return here.
            if "t" in value.lower():
                return True
            elif "f" in value.lower():
                return False

        # if the parameter is in vector_list_keys
        # These vectors are always floats
        elif parameter in vector_list_keys:
            # convert a string of...
            #   "x1 y1 z1 x2 y2 z2 x3 y3 z3"
            # to...
            #   [x1,y1,z1,x2,y2,z2,x3,y3,z3] (list of floats)
            # and then to...
            #   [[x1,y1,z1],[x2,y2,z2],[x3,y3,z3]]
            value = [float(item) for item in value.split()]
            return [value[i : i + 3] for i in range(0, len(value), 3)]

        # if the parameter is in float_list_keys
        elif parameter in float_list_keys:
            final_list = []
            for item in value.split():
                # Sometimes, the values are given as "3*0.1 2*0.5" where the "*"
                # means to include that value that many times. For example, this
                # input would be the same as "0.1 0.1 0.1 0.5 0.5". We need to
                # account for this when parsing.
                if "*" in item:
                    nsubitems, subitem = item.split("*")
                    for n in range(int(nsubitems)):
                        final_list.append(float(subitem))
                else:
                    final_list.append(float(item))
            return final_list

        # if the parameter is in int_list_keys
        elif parameter in int_list_keys:
            return [int(item) for item in value.split()]

        # If it is not in the common keys listed, just leave it as a string.
        else:
            return value

    def compare_incars(self, other_incar):
        """
        Compares two Incars and indicates which parameters are the same and
        which are not. Useful for checking whether two runs were done using
        the same parameters.
        Args:
            other (Incar): The other Incar object to compare to.
        Returns:
            Dict of the following format:
            {"Same" : parameters_that_are_the_same,
            "Different": parameters_that_are_different}
            The value of the other_incar is returned for the paramters that
            are different are returned as {Parameter: (incar_value, other_incar_value)}
            where None is used as a placeholder. For the same parameters, the
            dictionary is returned as {Parameter: shared_value}
        """

        same_parameters = {}
        different_parameters = {}

        # make a collection of all unique keys used by the two dictionaries
        # I convert to list() so I can use set() below.
        # OPTIMIZE -- is there a better way to do this?
        parameters1 = list(self.keys())
        parameters2 = list(other_incar.keys())

        # iterate through each unique parameter
        for parameter in set(parameters1 + parameters2):

            # try to grab the value from both Incar objects
            # If it doesn't have the value, None will be provided
            value1 = self.get(parameter)
            value2 = other_incar.get(parameter)

            # compare the two and store
            if value1 == value2:
                # it doesn't matter which value I grab so I just use value1
                same_parameters[parameter] = value1
            # if they are different...
            else:
                different_parameters[parameter] = (value1, value2)

        return {"Same": same_parameters, "Different": different_parameters}

    def __add__(self, other):
        """
        Add all the values of another INCAR object to this object.
        Facilitates the use of "standard" INCARs.
        """
        # start by copying this incar's settings
        new_parameters = dict(self.items())

        # now iterate through the other incar parameters to incorporate them
        for parameter, value in other.items():

            # If both have a given parameter, make sure they are the same values
            if parameter in self and value != self[parameter]:
                # If not, we shouldn't allow combining these Incars as it can
                # lead to undesired results.
                raise ValueError(
                    f"Incars have conflicting values! One conflict is with {parameter} "
                    f"where one incar has {self[parameter]} and the other has {value}"
                )
            # otherwise just set the value
            else:
                new_parameters[parameter] = value

        # now return the new Incar
        return Incar(**new_parameters)

    @classmethod
    def add_keyword_modifier(cls, keyword_modifier: Callable):
        """
        Dynamically sets a keyword_modifier function to the Incar class. When
        loaded onto the Incar class, you can then use the modifiers name to
        set a parameter based on the input structure.

        Names of modifiers MUST start with "keyword_modifier_" and
        have unique endings (i.e. you can't have 2 "per_atom" modifiers).

        For example, in order to allow settings like `ENCUT__per_atom`, we use
        a `keyword_modifier_per_atom` function and add it to this class:

        ``` python

        # create your modifier logic as a function
        def keyword_modifier_double_per_atom(structure, per_atom_value):
            return per_atom_value * structure.num_sites * 2

        # add it to the Incar class to make it active
        Incar.add_keyword_modifier(keyword_modifier_double_per_atom)

        # You can not use the modifier in incar logic!
        incar = Incar(ENCUT__double_per_atom=1e-5)
        ```
        """

        # first ensure that the modifier does not conflict with an existing one
        if hasattr(cls, keyword_modifier.__name__):
            raise Exception(
                "The Incar class already has a modifier with this name. "
                "Please use a different modifier name to avoid conflicts."
            )

        # add the function/callable as a static method to this class.
        # This line of code is based on...
        #   https://stackoverflow.com/questions/17929543/
        setattr(cls, keyword_modifier.__name__, staticmethod(keyword_modifier))


# set some default keyword modifiers
for modifier in [
    keyword_modifier_density,
    keyword_modifier_density_a,
    keyword_modifier_density_b,
    keyword_modifier_density_c,
    keyword_modifier_per_atom,
    keyword_modifier_smart_magmom,
    keyword_modifier_smart_lmaxmix,
    keyword_modifier_smart_ldau,
    keyword_modifier_smart_ismear,
]:
    Incar.add_keyword_modifier(modifier)
