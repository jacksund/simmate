# -*- coding: utf-8 -*-

from simmate.materials_science.elements import Element


class Species:
    """

    Species is an central class to using Simmate as there are many types that we
    need to account for. We use https://en.wikipedia.org/wiki/Chemical_species as
    a template for the type of species:
        atomic/elemental species --> This is just an Element with extra data
        ionic species --> an elemental species with an oxidation state
        molecular species -->  a moleucle object with extra data
        radical species --> species with unpaired electron
        compositional species --> similar to elemental species but with partial occupancy
            or with multiple elements & stoichiometric ratios



    Note all species can have extra data attached to it, but this *DOES NOT* include
    coordinates. This is generic data such as an ideal oxidation state or spin data.

    This class can be confusing when compared to Sites, which are Elements with
    extra data attached to each and *DOES* include coordinates.

    Deciding where to attach data (either Species or Site) can be tricky, but as
    a general rule, you should always use Site when working with Molecules and
    Structures -- and then use Species when you're working generically with a
    Composition.

    As an example, say I want to predict oxidation states. For the material Ca2NCl,
    I would make a Composition object made of Species, and each Species would have
    an oxidation state attached to it. For a crystal structure of Ca2NCl, I would
    want to instead attach oxidation states to each Site.

    As a bonus, if I wanted to switch from a Structure (made of Sites) to a generic
    Composition (made of Species), I can use a Structure's composition attribute to
    get a Composition object. This would group all of the Sites by their unique
    properties (ignoring coordinates) and give you a list of the unique Species.

    For extra help, use this tutorial or you can ask our team about your situation:
        < TODO: ADD LINK >
    """

    def __init__(self, symbol, oxidation_state=0.0, **kwargs):

        # Because oxidation states are the most commonly used with Species objects,
        # I set that keyword, but all others can be defined by the user. Here are
        # some standard keywords worth considering:
        #   oxidation_state
        #   spin_up / spin_down / spin_total
        #   population

        # for each additional keyword and value provided, link it to an attribute
        pass
