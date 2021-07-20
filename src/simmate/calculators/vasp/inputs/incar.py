# -*- coding: utf-8 -*-


class Incar(dict):
    """
    INCAR object for reading and writing INCAR files. This behaves exactly like
    a python dictionary, but has a few extra checks and methods attached to it.
    You can pass it a dictionary or initialize it just like you would dict(kwargs).
    You can consider the dict(kwargs) as equivalent to Incar(parameters).
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
            formatted_value = self._str_to_datatype(parameter, value)
            self.update({parameter: formatted_value})

        # SPECIAL CASE
        # If you have LSORBIT=True or LNONCOLLINEAR=True, the MAGMOM class needs
        # to take on a different form. Instead of a single MAGMOM being set as
        # a float, it's now a vector (x,y,z). For example:
        #   MAGMOM = x1 y1 z1    x2 y2 z2    x3 y3 z3 ...
        #       [...instead of...]
        #   MAGMOM = value1 value2 value3 ...
        # TODO: is this the best implementation spot? What about where I parse
        # all other values to their target format and shapes?

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

    def __str__(self):

        # Let's start with an empty string and build from there
        final_str = ""

        # Iterate through each parameter and its set value. Each one will be
        # put on a separate line.
        for parameter, value in self.items():

            # let's start by adding the parameter key to our output
            # It will be followed by an equal sign to separate it's value
            final_str += parameter + " = "

            # If we have a value that is a list (or list of lists)
            if isinstance(value, list):

                # check if we have a list of lists, which is uncommon
                # Take MAGMOM with LSORBIT=True as an example, where we convert...
                #   [[x1,y1,z1],[x2,y2,z2],[x3,y3,z3]]
                # to...
                # "x1 y1 z1 x2 y2 z2 x3 y3 z3"
                # !!! Should I do "x1 y1 z1\tx2 y2 z2\tx3 y3 z3"
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

    def to_file(self, filename="INCAR"):
        """
        Write Incar to a file.
        Args:
            filename (str): filename to write to.
        """
        # we just take the string format and put it in a file
        with open(filename, "w") as file:
            file.write(self.__str__())

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
        val string to the proper python datatype (int,float, bool, list...).
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
            return [float(item) for item in value.split()]

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
                same_parameters.update({parameter: value1})
            # if they are different...
            else:
                different_parameters.update({parameter: (value1, value2)})

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
                raise ValueError("Incars have conflicting values!")
            # otherwise just set the value
            else:
                new_parameters[parameter] = value

        # now return the new Incar
        return Incar(**new_parameters)
