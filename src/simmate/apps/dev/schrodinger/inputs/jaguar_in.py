# -*- coding: utf-8 -*-

from pathlib import Path

from simmate.toolkit import Molecule


class JaguarInput:
    """
    The general input file format for Jaguar calculations. Currently, we only
    support inputs for Jaguar pKa, but this class can easily be extented to
    include other calculation types.

    The only two sections needed for pKa are:
        - zmat
        - gen

    A basic input file looks like:
    ```
    &zmat
      C1   1.0590559100      0.0794463600      0.3608319800
      O2   0.8609619100      1.1054614700     -0.2390046100
      O3   2.2130316700     -0.6129886300      0.3489813100
      H1   2.8258867600     -0.1221771000     -0.2269021000
      H2   0.3281776900     -0.4358328800      1.0011835800
    &
    &gen
    ipka_prot_deprot=both
    ipkasearch=all
    ipka_solv_opt=1
    ipka_max_conf=10
    ipka_csrch_acc=1
    &
    ```

    The python equivalent of this would be:
    ``` python
    JaguarInput(
        molecule=..., # Molecule object match what is in zmat section
        gen=dict(
            ipka_prot_deprot="both",
            ipkasearch="all",
            ipka_solv_opt=1,
            ipka_max_conf=10,
            ipka_csrch_acc=1,
        ),
    )
    ```

    See official docs on the input file at:
     - https://learn.schrodinger.com/private/edu/release/current/Documentation/html/jaguar/jaguar_command_reference/jaguar_input.htm
    """

    PARAMETER_SECTIONS = [
        "&gen",  # key-value pairs with key settings
        "&zmat",  # molecule info. similar to XYZ
    ]

    # establish type mappings for common parameters.
    # See:
    #   https://learn.schrodinger.com/private/edu/release/current/Documentation/html/jaguar/jaguar_command_reference/jaguar_input_gen_pka.htm
    PARAMETER_MAPPINGS = {
        "ipkat": str,
        "ipkasites": list[str],
        "ipkasearch": list[str],
        "ipka_prot_deprot": str,
        "ipka_lower_cut": float,
        "ipka_upper_cut": float,
        "ipka_tier_cutoff": int,
        "ipkaraw": int,  # really a boolean 0/1
        "ipka_max_conf": int,
        "ipka_erg_window": float,
        "ipkaverbose": int,  # really a boolean 0/1
        "ipka_csrch_acc": int,  # really a boolean 0/1
        "ipka_solv_opt": int,  # really a boolean 0/1
        "ipka_frac_gconf": float,
        "ipkasymm": int,  # really a boolean 0/1
    }

    def __init__(
        self,
        molecule: Molecule,
        gen: dict,
        convert_to_3d: bool = False,
    ):

        # BUG: should I copy the structure since we are modifying it?
        self.molecule = molecule
        self.gen = gen

        # jaguar requires hydrogen atoms to be present
        self.molecule.add_hydrogens()

        # This workflow requires a 3D conformer input. Ideally, the user provides
        # one, but we can also generate a rough 3D conformer which works well too
        if convert_to_3d:
            self.molecule.convert_to_3d(keep_hydrogen=True)

    def to_str(self) -> str:
        # NOTE: we don't enable any modifiers for this input file (e.g. __per_atom).
        # See QE and VASP inputs if I ever want to add this.

        final_str = ""

        # ----------------------

        # place key-value gen section up top

        # section title
        final_str += "&gen\n"
        # settings
        for key, value in self.gen.items():
            final_str += f"{key}={value}\n"
        # section ending
        final_str += "&\n"

        # ----------------------

        # then write molecule information in zmat section

        # section title
        final_str += "&zmat\n"
        # XYZ-like list of atoms
        # TODO: should this be its own file_converter.Adaptor in the toolkit?
        for atom in self.molecule.atom_list:
            name = atom["element"] + str(atom["index"] + 1)
            # BUG: Maybe limit to 10 decimal places with f"{c:.10f}". Zmat fails
            # if the row is >70 characters
            coords = "\t".join([str(c) for c in atom["coords"]])
            final_str += f"{name}\t{coords}\n"
        # section ending
        final_str += "&\n"

        # ----------------------

        return final_str

    def to_file(self, filename: Path | str = "settings.in"):
        filename = Path(filename)
        with filename.open("w") as file:
            file.write(self.to_str())
