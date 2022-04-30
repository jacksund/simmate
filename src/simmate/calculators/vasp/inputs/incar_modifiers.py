# -*- coding: utf-8 -*-

import math

from simmate.toolkit import Structure

# TODO: consider making modifiers a class. For example:
#
# class PerAtom(KeywordModifier):
#     tag_name = "__per_atom"
#     @staticmethod
#     def apply(structure, per_atom_value):
#         return per_atom_value * structure.num_sites


def keyword_modifier_density(structure: Structure, density: float):
    """
    The __density modifier means the user wants a specific density. They
    provide this density in per-angstrom^3 units and we return the
    structure-specific count that gives this density.
    For example, density=10 and a structure lattice that volume of 5,
    then this returns value=10*5=50.
    """
    # VASP expect integers for a lot of these values, so we round up
    return math.ceil(structure.lattice.volume * density)


def keyword_modifier_density_a(structure: Structure, density: float):
    """
    The __density_a modifier means the user wants a specific density along
    the A lattice vector. They provide this density in per-angstrom units
    and we return the structure-specific count that gives this density.
    For example, density=10 and a structure lattice that A vector of 5,
    then this returns value=10*5=50.
    """
    # VASP expect integers for a lot of these values, so we round up
    return math.ceil(structure.lattice.a * density)


def keyword_modifier_density_b(structure: Structure, density: float):
    return math.ceil(structure.lattice.b * density)


def keyword_modifier_density_c(structure: Structure, density: float):
    return math.ceil(structure.lattice.c * density)


def keyword_modifier_per_atom(structure: Structure, per_atom_value: float):
    """
    The __per_atom modifier means the user wants a specific value per atom
    in the unit cell. For example, EDIFF__per_atom=1e-5 and a structure
    with 50 sites in it would return a value of 1e-5*50=50.
    """
    return per_atom_value * structure.num_sites


def keyword_modifier_smart_magmom(structure: Structure, override_values: dict):
    """
    The __smart_magmom modifier goes through a series of checks to decide
    what to set the MAGMOM as for VASP. In order of priority they are...
        (1) the magmom property attached to each site in the structure object
        (2) the spin property attached to the site's specie
        (3) a value provided explicitly (e.g. {"Co": 0.5})
        (4) a value of 0.6
    """

    # grab the default MAGMOM supplied, or use VASP's default of 1 otherwise
    default_value = override_values.get("default", 1)

    # we go through each site in the structure and decide what to set the
    # MAGMOM for each. This allows even different sites of the same
    # element to have their own MAGMOM
    magnetic_moments = []
    for site in structure:
        # if the structure object has magmom-decorated sites, we use that
        # as our first priority
        if hasattr(site, "magmom"):
            magnetic_moments.append(site.magmom)
        # next we check if the site's specie has a spin
        elif hasattr(site.specie, "spin"):
            magnetic_moments.append(site.specie.spin)
        # we then look at the override dictionary if there was one provided.
        # If note, we use 0.6 as a default.
        else:
            magnetic_moment = override_values.get(site.specie.symbol, default_value)
            magnetic_moments.append(magnetic_moment)

    # This feature is in pymatgen, but I haven't added it here yet.
    # if self.constrain_total_magmom:
    #     nupdown = sum([mag if abs(mag) > 0.6 else 0 for mag in incar["MAGMOM"]])
    #     incar["NUPDOWN"] = nupdown

    return magnetic_moments


def keyword_modifier_smart_lmaxmix(structure: Structure, lmaxmix_config: bool):
    """
    This modifier sets LMAXMIX if there are any d or f electrons present
    in the structure.
    """

    # COMMENT (from pymatgen team):
    # Note that if the user explicitly sets LMAXMIX in settings it will
    # override this logic.
    # Previously, this was only set if Hubbard U was enabled as per the
    # VASP manual but following an investigation it was determined that
    # this would lead to a significant difference between SCF -> NonSCF
    # even without Hubbard U enabled. Thanks to Andrew Rosen for
    # investigating and reporting.

    # first iterate through all elements and check for f-electrons
    if any(element.Z > 56 for element in structure.composition):
        return 6
    # now check for elements that contain d-electrons
    elif any(element.Z > 20 for element in structure.composition):
        return 4
    # otherwise use the default for VASP
    else:
        return None  # default is 2, but we don't set it


def keyword_modifier_smart_ldau(structure: Structure, ldau_config: dict):
    """
    This modifier handles a series of keyword arguments that are associated
    with LDAU, including LDAUJ, LDAUL, LDAUTYPE, LDAUU, and LDAUPRINT.
    Therefore, a complex dictionary is passed to this. The format looks
    like this...
        LDAU__multiple_keywords__smart_ldau = dict(
            LDAU__auto=True,
            LDAUTYPE=2,
            LDAUPRINT=1,
            LDAUJ={...},
            LDAUL={...},
            LDAUU={...},
            )
    The LDAUJ, LDAUL, and LDAUU values can be a dictionary of elements to
    value, or (most commonly) a nested dictionary. For example...
        LDAUJ = {"F":{"Co":0}}
    This would mean if the structure is a fluoride, set the LDAUJ for Co to 0.
    If there are multiple options here (e.g. for fluorides and oxides), then
    priority is placed on the most electronegative element. This would mean
    some thing like yttrium oxide fluoride would be treated as a fluoride over
    an oxide.
    """

    # first we need to go through the LDAUJ, LDAUL, and LDAUU keywords and
    # see what their values are. If all of these end up be 0 for all elements
    # then we actually don't need LDAU at all! Therefore, we'll go through
    # all of these keywords and build a dictionary of settings to return
    # at the end of this function
    ldau_settings = {}

    # To help decide how we set these values, let's check what the most
    # electronegative element is, which will be last in the sorted composition
    most_electroneg = sorted(structure.composition.elements)[-1].symbol

    # As we go through these settings, we want see if we are even using LDAU.
    # For example if we ran a calculation on NaCl, we'd probably see that
    # all LDAUJ/LDAUL/LDAUU values are just 0. In that case, we can just
    # throw away (i.e. turn off) all LDAU settings. Therefore, we have a term
    # "using_ldau" that is false until proven otherwise.
    using_ldau = False

    for ldau_keyword in ["LDAUJ", "LDAUL", "LDAUU"]:

        # grab the sub-dictionary that maps elements to this keyword.
        # If it's not there, just use an empty dictionary.
        keyword_config = ldau_config.get(ldau_keyword, {})

        # check if the most electronegative element is in the override_values
        # and if so, see if it has a subdictionary in it. We use this
        # dictionary as our base one to pull values from.
        if most_electroneg in keyword_config and isinstance(
            keyword_config[most_electroneg], dict
        ):
            keyword_config = keyword_config[most_electroneg]

        # now iterate through all the sites and grab the assigned value. If nothing
        # is set then the default is 0.
        values = [
            keyword_config.get(element.symbol, 0) for element in structure.composition
        ]

        # now that we have this keyword all set, we add it to our results
        ldau_settings[ldau_keyword] = values

        # check to see if we are using ldau here (i.e. any value is not 0)
        if any(values):
            using_ldau = True

    # now check if we actaully need LDAU here. If not, we can throw out all
    # settings and just return an empty dictionary
    if using_ldau and "LDAU__auto" in ldau_config:
        ldau_settings["LDAU"] = True
    else:
        return {}

    # The remaining LDAU keywords are LDAUPRINT and LDAUTYPE, which we just
    # leave at what is set in the input
    if "LDAUPRINT" in ldau_config:
        ldau_settings["LDAUPRINT"] = ldau_config["LDAUPRINT"]
    if "LDAUTYPE" in ldau_config:
        ldau_settings["LDAUTYPE"] = ldau_config["LDAUTYPE"]

    return ldau_settings


def keyword_modifier_smart_ismear(structure: Structure, ismear_config: dict):
    """
    The smearing value used here depends on if we have a semiconductor,
    insulator, or metal. This modifier makes a "best-guess" on what the
    material is and uses the proper smearing type. Note that if this
    guess is wrong, it is useful to have the IncorrectSmearing error
    handler to fix this as VASP runs.

    Read more about the VASP recommended ISMEAR settings here:
        https://www.vasp.at/wiki/index.php/ISMEAR
    """

    # for now we just go through the structure and if all elements are
    # metals, then we say it's a metal. Otherwise, we treat the structure
    # as a semiconductor or insulator.
    if all(element.is_metal for element in structure.composition):
        ismear_settings = ismear_config.get("metal", {})

    else:
        ismear_settings = ismear_config.get("non-metal", {})

    return ismear_settings


# TODO: In the future, I want to allow modifiers like __relative_to_previous
# and __use_previous to string settings accross tasks.

# To introduce other modifiers that pymatgen uses...
# https://github.com/materialsproject/pymatgen/blob/b789d74639aa851d7e5ee427a765d9fd5a8d1079/pymatgen/io/vasp/sets.py#L500

# if self.use_structure_charge:
#     incar["NELECT"] = self.nelect

# Ensure adequate number of KPOINTS are present for the tetrahedron
# method (ISMEAR=-5). If KSPACING is in the INCAR file the number
# of kpoints is not known before calling VASP, but a warning is raised
# when the KSPACING value is > 0.5 (2 reciprocal Angstrom).
# An error handler in Custodian is available to
# correct overly large KSPACING values (small number of kpoints)
# if necessary.
# if "KSPACING" not in self.user_incar_settings.keys():
# if self.kpoints is not None:
#     if np.product(self.kpoints.kpts) < 4 and incar.get("ISMEAR", 0) == -5:
#         incar["ISMEAR"] = 0
