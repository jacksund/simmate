# -*- coding: utf-8 -*-

from pathlib import Path

from simmate.apps.vasp.inputs.incar_modifiers import (
    keyword_modifier_density,
    keyword_modifier_density_a,
    keyword_modifier_density_b,
    keyword_modifier_density_c,
    keyword_modifier_per_atom,
    keyword_modifier_smart_ismear,
    keyword_modifier_smart_ldau,
    keyword_modifier_smart_lmaxmix,
    keyword_modifier_smart_magmom,
    keyword_modifier_smart_quad_efg,
)
from simmate.toolkit import Structure
from simmate.utilities import str_to_datatype


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

    # establish type mappings for common INCAR parameters
    PARAMETER_MAPPINGS = {
        # BOOLEANS
        "LDAU": bool,
        "LWAVE": bool,
        "LSCALU": bool,
        "LCHARG": bool,
        "LPLANE": bool,
        "LUSE_VDW": bool,
        "LHFCALC": bool,
        "ADDGRID": bool,
        "LSORBIT": bool,
        "LNONCOLLINEAR": bool,
        "KGAMMA": bool,
        # FLOATS
        "EDIFF": float,
        "SIGMA": float,
        "TIME": float,
        "ENCUTFOCK": float,
        "HFSCREEN": float,
        "POTIM": float,
        "EDIFFG": float,
        "AGGAC": float,
        "PARAM1": float,
        "PARAM2": float,
        "KSPACING": float,
        "SYMPREC": float,
        "AMIX": float,
        "BMIX": float,
        "AMIN": float,
        "SMASS": float,
        "AMIX_MAG": float,
        "BMIX_MAG": float,
        # INTEGERS
        "NSW": int,
        "NBANDS": int,
        "NELMIN": int,
        "ISIF": int,
        "IBRION": int,
        "ISPIN": int,
        "ICHARG": int,
        "NELM": int,
        "ISMEAR": int,
        "NPAR": int,
        "LDAUPRINT": int,
        "LMAXMIX": int,
        "ENCUT": int,
        "NSIM": int,
        "NKRED": int,
        "NUPDOWN": int,
        "ISPIND": int,
        "LDAUTYPE": int,
        "IVDW": int,
        "ISTART": int,
        "NELMDL": int,
        "IMIX": int,
        "ISYM": int,
        # LIST OF INTEGERS
        "LDAUL": list[int],
        # LIST OF FLOATS
        "LDAUU": list[float],
        "LDAUJ": list[float],
        "MAGMOM": list[float],  # depends on other args -- see notes in init
        "LANGEVIN_GAMMA": list[float],
        "QUAD_EFG": list[float],
        "EINT": list[float],
        # LIST OF VECTORS
        # "MAGMOM",  # depends on other args -- see notes in init
        "DIPOL": list[list[float]],
    }

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
                formatted_value = str_to_datatype(
                    parameter,
                    value,
                    self.PARAMETER_MAPPINGS,
                )
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

    def to_evaluated_str(self, structure: Structure = None):
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

    def to_file(
        self,
        filename: Path | str = "INCAR",
        structure: Structure = None,
    ):
        """
        Write Incar to a file.
        Args:
            filename (str): filename to write to.
        """
        # we just take the string format and put it in a file
        filename = Path(filename)
        with filename.open("w") as file:
            file.write(self.to_evaluated_str(structure=structure))

    @classmethod
    def from_file(cls, filename: Path | str = "INCAR"):
        """
        Builds an Incar object from a file.
        """
        filename = Path(filename)
        with filename.open() as file:
            content = file.read()
        return cls.from_str(content)

    @classmethod
    def from_str(cls, content: str):
        """
        Builds an Incar object from a string.
        """
        # split the file content into separate lines
        lines = content.split("\n")

        # store parameters in this dictionary
        parameters = {}
        # go through line by line
        for line in lines:
            # If the line starts with a # then its a comment and we should skip.
            # It also could be an empty line that we should skip,
            if not line or line.startswith("#") or line.startswith("\n"):
                continue
            # multiple parameters on a single line are separated by a semicolon
            for sub_line in line.split(";"):
                # the PARAMETER and VALUE are separated by equal sign
                parameter, value = sub_line.split("=")
                # we can use the parameter/value to update our dictionary. The
                # last thing we do is remove leading/trailing whitespace with strip()
                parameters[parameter.strip()] = value.strip()

        # return the final dictionary as an Incar object
        return cls(**parameters)

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
    def add_keyword_modifier(cls, keyword_modifier: callable):
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
    keyword_modifier_smart_quad_efg,
]:
    Incar.add_keyword_modifier(modifier)
