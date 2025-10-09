# -*- coding: utf-8 -*-

from pathlib import Path

from simmate.utilities import str_to_datatype


class OmegaParm(dict):
    """
    Set of input parameters for Omega. This behaves exactly like
    a python dictionary, but has a few extra checks and methods attached to it.
    You can pass it a dictionary or initialize it just like you would dict(kwargs).
    You can consider the dict(kwargs) as equivalent to OmegaParm(parameters).

    Example use:
    ```python
    from simmate.apps.openeye_omega.inputs import OmegaParm

    settings = OmegaParm(
        in_="input.sdf",
        out="output.oez",
        commentEnergy=True,
        maxConfs=10,
        flipper=True,
        flipper_maxcenters=4,
        progress="percent",
        # mpi_np=10,  BUG: this setting cannot be done in the commandline
    )

    settings.to_file()
    settings_new = settings.from_file()
    ```
    """

    # establish type mappings for all parameters
    # see https://docs.eyesopen.com/applications/omega/omega/omega_opt_params.html
    PARAMETER_MAPPINGS = {
        # Required Parameters
        "in": str,  # Path
        # Execute parameters
        "param": str,  # Path (this is the parameter file and should be set by Simmate)
        "mpi_np": int,
        "mpi_hostfile": str,  # Path
        # File Parameters
        "out": str,  # Path
        "commentEnergy": bool,
        "includeInput": bool,
        "log": str,  # Path
        "prefix": str,
        "progress": str,
        "rotorOffsetCompress": bool,
        "sdEnergy": bool,
        "verbose": bool,
        "warts": bool,
        # 3D Construction Parameters
        "addfraglib": str,  # Path
        "setfraglib": str,  # alias to addfraglib
        "buildff": str,
        "canonOrder": bool,
        "deleteFixHydrogens": bool,
        "fixfile": str,  # Path
        "fixrms": float,
        "fixsmarts": str,  # !!! unsure here...
        "fixmcs": bool,
        "fromCT": bool,
        "maxmatch": int,
        "mcsMinAtoms": int,
        "strictfrags": bool,
        "strictatomtyping": bool,
        "umatch": bool,
        # Structure Enumeration Parameters
        "enumNitrogen": str,
        "enumRing": bool,
        "sampleHydrogens": bool,
        # Torsion Driving Parameters
        "addtorlib": str,
        "erange": list[float],
        "ewindow": float,
        "maxConfRange": list[float],
        "maxConfs": int,  # !!! typo in omega docs for capitalization?
        "maxrot": int,
        "maxtime": float,
        "rangeIncrement": int,
        "rms": float,
        "rmsrange": list[float],
        "searchff": str,
        "settorlib": str,  # Path
        "torlibtype": str,
        "useGPU": bool,
        # Stereo Parameters
        "flipper": bool,
        "flipper_maxcenters": int,
        "flipper_warts": bool,
        "flipper_enhstereo": bool,
        "strictstereo": bool,
        # Other
        "strict": bool,
    }

    def __init__(self, **kwargs):
        # Establish the dictionary with the given input
        # This is the same as doing dict(**kwargs)
        super().__init__(**kwargs)

        # BUG: "in" is a reserved python expression, so it can't be used.
        # We there for need to input "in_" as the parameter instead
        if "in_" in self.keys():
            value = self.pop("in_")  # remove from dict
            self.update({"in": value})  # and rename the input

        # Based on the kwargs, go through and make sure each parameter is in
        # it's expected datatype.
        for parameter, value in self.items():
            formatted_value = str_to_datatype(
                parameter,
                value,
                self.PARAMETER_MAPPINGS,
            )
            self.update({parameter: formatted_value})

    def to_str(self) -> str:
        # TODO: consider dynamic settings (see to_evaluated_str in VASP's Incar)
        # TODO: refactor as much of this code is copy/pasted fron Incar method

        # Let's start with an empty string and build from there
        final_str = ""

        # Now that we have all of our parameters evaluated for the structure, we
        # iterate through each parameter and its set value. Each one will be
        # put on a separate line.
        for parameter, value in self.items():
            # let's start by adding the parameter key to our output
            # It will be followed by an equal sign to separate it's value
            final_str += f"-{parameter} "

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

            # The "lower" is for True/False --> true/false
            elif isinstance(value, bool):
                final_str += str(value).lower()

            # if it's not a list or bool, we can just save the string of the value.
            else:
                final_str += str(value).lower()

            # we want to start each parameter on a new line, so we need to
            # add this at the end of each. There will be an extra new line at
            # the end of the file, but that's alright
            final_str += "\n"

        # we now have our final string and can return it!
        return final_str

    def to_file(self, filename: Path | str = "parameters.txt"):
        # we just take the string format and put it in a file
        filename = Path(filename)
        with filename.open("w") as file:
            file.write(self.to_str())

    @classmethod
    def from_file(cls, filename: Path | str = "parameters.txt"):
        # open the file, grab the lines, and then close it
        filename = Path(filename)
        with filename.open() as file:
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
                # the PARAMETER and VALUE are separated by a space
                parameter = sub_line.split(" ")[0][1:]
                value = "".join(sub_line.split(" ")[1:])
                # we can use the parameter/value to update our dictionary. The
                # last thing we do is remove leading/trailing whitespace with strip()
                parameters[parameter.strip()] = value.strip()

        # return the final dictionary as an python object
        return cls(**parameters)
