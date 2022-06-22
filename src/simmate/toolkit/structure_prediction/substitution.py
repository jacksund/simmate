# -*- coding: utf-8 -*-

import itertools
from typing import List

from pymatgen.core import Species
from pymatgen.analysis.structure_prediction.substitutor import Substitutor

from simmate.toolkit import Composition, Structure
from .known import get_known_structures


def get_structures_from_substitution_of_known(
    composition: Composition,
    **kwargs,  # passed to get_known_structures
) -> List[Structure]:
    """
    Predicts the most likely element substitutions for a composition, and then
    based off the predictions, it will go through all database tables in the
    `simmate.database.third_parties` module generate substituted structures.

    Each database table must be populated -- otherwise this function will
    return an empty list.
    """

    # make sure the composition has oxidation states and if not, add states
    # using the built-in guessing method
    if not isinstance(composition.elements[0], Species):
        oxi_composition = composition.add_charges_from_oxi_state_guesses()
    else:
        # make a copy just in case we perform manipulations below
        oxi_composition = composition.copy()

    # and grab the list of species, which we will need later
    elements_final = [str(element) for element in oxi_composition]
    oxi_states = {
        element.symbol: element.oxi_state for element in oxi_composition.elements
    }

    # init the substitution engine and grab the list of likely substituitions
    substitutor = Substitutor()

    # ----------
    # BUG: This code should be a single line:
    #   expected_substituitions = substitutor.pred_from_comp(oxi_composition)
    # Howevever, pymatgen's function fails when even a single element is not
    # allowed with their dataset (e.g. any carbides will fail). To get around
    # this, I use pred_from_list instead of pred_from_comp, and I keep trying
    # until I get one that works. The while loop here is try every combination
    # of elements (starting with all of them and then try smaller combos) and
    # exits as soon as I find one that works.
    nelements = len(oxi_composition.elements)
    has_subs = False
    while (not has_subs) and (nelements > 0):
        for elements_to_sub in itertools.combinations(
            oxi_composition.elements, nelements
        ):
            try:
                expected_substituitions = substitutor.pred_from_list(elements_to_sub)
                break  # exit immediately once successful
            except:
                expected_substituitions = None
        if expected_substituitions:
            has_subs = True
        else:
            # try the cycle again but with one less element in the combinations
            nelements -= 1

    if not expected_substituitions:
        raise Exception("Failed to find viable substituitions for this composition")

    # Confirm charge balance for most-likely structures
    # This loop is copy/pasted from...
    # https://github.com/materialsproject/pymatgen/blob/e0c1ee845e7131213055c5b4fc6df2cb12fcc667/pymatgen/analysis/structure_prediction/substitutor.py#L238
    output = []
    for p in expected_substituitions:
        subs = p["substitutions"]
        charge = 0
        for i_el in oxi_composition.elements:
            f_el = subs[i_el]
            charge += f_el.oxi_state * oxi_composition[i_el]
        if charge == 0:
            output.append(p)
    expected_substituitions = output

    # ----------

    # Keep a list of all structures that we create
    structures_final = []

    # now iterate through the expected substitutions, grab the known structures
    # from databases, and then perform the substitution to generate new structures
    for substituition in expected_substituitions:

        # The methods below expect this sub dictionary to be based off of strings
        # instead of Species objects, so we convert them first.
        substituition_cleaned = {
            str(element_new): str(element_orig)
            for element_new, element_orig in substituition["substitutions"].items()
        }
        # this is the same as above with keys/values flipped
        substituition_cleaned_2 = {
            str(element_orig): str(element_new)
            for element_new, element_orig in substituition["substitutions"].items()
        }

        # Generate the composition that we will use for source structures
        composition_source = oxi_composition.replace(substituition_cleaned.copy())
        # BUG: this method is destructive to the input dictionary so we must
        # pass a copy instead
        print([oxi_composition, composition_source, substituition_cleaned])

        # Now grab all known structures with this composition
        source_structures = get_known_structures(composition_source, **kwargs)

        # skip to the next substitution type if no structures were found
        if not source_structures:
            continue

        # grab the oxidation states from our original substituition
        oxi_states_sub = {
            element_orig.symbol: element_orig.oxi_state
            for element_new, element_orig in substituition["substitutions"].items()
        }
        # in case oxi_states_sub does not contain all of the elements of the
        # composition (see the itertools.combinations loop above), then we
        # need to add back the oxi state of missing elements here.
        for key, value in oxi_states.items():
            if key not in oxi_states_sub:
                oxi_states_sub[key] = value

        # decorate the structure with these oxi states
        for structure in source_structures:
            structure.add_oxidation_state_by_element(oxi_states_sub)

        # BUG: this is the method that's built-in with the Substitutor class,
        # but it throws random errors and also is more code... I do away with
        # this for now, but keep the code fore reference.
        #
        # finally, use this list of structures to generate sub structures. this
        # method requires the input structures to be given as a dictionary
        # structure_list = [
        #     {"structure": structure, "id": structure.database_object.id}
        #     for structure in source_structures
        # ]
        # new_structures = substitutor.pred_from_structures(
        #     target_species=elements_final,
        #     structures_list=structure_list,
        # )
        # # clean these new structures
        # for structure in new_structures:
        #     # note, structure is a TransformedStructure obj to start
        #     structure_final = structure.final_structure
        #     structure_final.remove_oxidation_states()
        #     structures_final.append(structure_final)

        for structure in source_structures:
            new_structure = structure.copy()
            new_structure.replace_species(substituition_cleaned_2)
            # TODO: scale structures to reasonable volume..?
            structures_final.append(new_structure)

    return structures_final
