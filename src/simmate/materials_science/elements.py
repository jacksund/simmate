# -*- coding: utf-8 -*-

from enum import Enum

from simmate.materials_science.element_data import ALL_DATA, SUPPORTED_PROPERTIES


class Element(Enum):
    """
    The Element class is really just a dictionary of fixed data, but we perform some
    extra python "tricks" to help with performance.

    WARNING: This class implements some advanced python topics, and you don't need
    to understand them to use this class as a beginner. Beginners should check out
    element_data.py (and the csv file) to see which data is available. Also look
    at this link for a quick tutorial:
        << TODO: INSERT LINK >>

    The main performance boost comes from making this a subclass of Enum, which
    means there are fixed number of options to choose from. Further, once one is
    chosen, it never changes! This means we really only need one object instance
    for each element -- and any time we call Element("H"), it will share that instance
    and data. This is effectively a "singleton" and helps us save on memory in a big way.

    The second thing we do is "lazy-loading" of an Element's attributes. This helps
    with how fast we can create Element objects. In 99% of cases, we really don't need
    all of the data about an element -- just the symbol. Therefore, data isn't loaded
    and attached to Element objects until they need to be. One you call that attribute
    once, we then link it to the object and it's there for good. This helps with performance
    too because once an attribute is accessed, it will likely be accessed again.
    """

    # These are the only possible Elements. Any other inputs for this class will
    # raise an error. Note, we also include a dummy element for when a site needs
    # to be specified without assigning an element to it: this is Unknown = "X"
    Unknown = "X"
    Hydrogen = "H"
    Helium = "He"
    Lithium = "Li"
    Beryllium = "Be"
    Boron = "B"
    Carbon = "C"
    Nitrogen = "N"
    Oxygen = "O"
    Fluorine = "F"
    Neon = "Ne"
    Sodium = "Na"
    Magnesium = "Mg"
    Aluminum = "Al"  # This is the correct spelling. Fight me about it.
    Silicon = "Si"
    Phosphorus = "P"
    Sulfur = "S"
    Chlorine = "Cl"
    Argon = "Ar"
    Potassium = "K"
    Calcium = "Ca"
    Scandium = "Sc"
    Titanium = "Ti"
    Vanadium = "V"
    Chromium = "Cr"
    Manganese = "Mn"
    Iron = "Fe"
    Cobalt = "Co"
    Nickel = "Ni"
    Copper = "Cu"
    Zinc = "Zn"
    Gallium = "Ga"
    Germanium = "Ge"
    Arsenic = "As"
    Selenium = "Se"
    Bromine = "Br"
    Krypton = "Kr"
    Rubidium = "Rb"
    Strontium = "Sr"
    Yttrium = "Y"
    Zirconium = "Zr"
    Niobium = "Nb"
    Molybdenum = "Mo"
    Technetium = "Tc"
    Ruthenium = "Ru"
    Rhodium = "Rh"
    Palladium = "Pd"
    Silver = "Ag"
    Cadmium = "Cd"
    Indium = "In"
    Tin = "Sn"
    Antimony = "Sb"
    Tellurium = "Te"
    Iodine = "I"
    Xenon = "Xe"
    Caesium = "Cs"
    Barium = "Ba"
    Lanthanum = "La"
    Cerium = "Ce"
    Praseodymium = "Pr"
    Neodymium = "Nd"
    Promethium = "Pm"
    Samarium = "Sm"
    Europium = "Eu"
    Gadolinium = "Gd"
    Terbium = "Tb"
    Dysprosium = "Dy"
    Holmium = "Ho"
    Erbium = "Er"
    Thulium = "Tm"
    Ytterbium = "Yb"
    Lutetium = "Lu"
    Hafnium = "Hf"
    Tantalum = "Ta"
    Tungsten = "W"
    Rhenium = "Re"
    Osmium = "Os"
    Iridium = "Ir"
    Platinum = "Pt"
    Gold = "Au"
    Mercury = "Hg"
    Thallium = "Tl"
    Lead = "Pb"
    Bismuth = "Bi"
    Polonium = "Po"
    Astatine = "At"
    Radon = "Rn"
    Francium = "Fr"
    Radium = "Ra"
    Actinium = "Ac"
    Thorium = "Th"
    Protactinium = "Pa"
    Uranium = "U"
    Neptunium = "Np"
    Plutonium = "Pu"
    Americium = "Am"
    Curium = "Cm"
    Berkelium = "Bk"
    Californium = "Cf"
    Einsteinium = "Es"
    Fermium = "Fm"
    Mendelevium = "Md"
    Nobelium = "No"
    Lawrencium = "Lr"
    Rutherfordium = "Rf"
    Dubnium = "Db"
    Seaborgium = "Sg"
    Bohrium = "Bh"
    Hassium = "Hs"
    Meitnerium = "Mt"
    Darmstadtium = "Ds"
    Roentgenium = "Rg"
    Copernicium = "Cn"
    Nihonium = "Nh"
    Flerovium = "Fl"
    Moscovium = "Mc"
    Livermorium = "Lv"
    Tennessine = "Ts"
    Oganesson = "Og"

    def __init__(self, symbol):

        self.symbol = symbol

        # OPTIMIZE: consider adding key attributes here for speed. The cost of
        # adding upfront is ___ns while adding later costs ___ns
        # I could have an enviornment variable so users can set this directly too.
        # That would be advanced usage, but may be useful to some.

    def __getattr__(self, item):
        """
        This function is only called when "self.item" fails. It therefore
        takes longer than if you were to set the attribute in the init. However,
        more often than not, we don't need the attributes set prior. We do this
        to speed up the initialization of Element objects. This ends up being a
        problem later if the user is constantly trying to access an attribute that
        wasn't pre-set. As a solution to that, we set the attributes as they
        are accessed -- via the setattr() function. This means the first call takes
        longer and then it's fast after that. If I never access this attribute again,
        this is also wasted overhead. I should do more testing as to whether this
        line is actually beneficial or not.
        """

        # See if the requested attribute is actually one we support
        if item in SUPPORTED_PROPERTIES:

            # Grab our target data
            # NOTE: I am using data.get(item) instead of data[item] because I want
            # to return None when the data is available. This is slower but gives
            # our desired effect.
            value = ALL_DATA[self.symbol].get(item)

            # Set the attribute to the data so we can access it quickly in the future.
            setattr(self, item, value)

            # And now that everything is set up, return the target value to the user
            return value

        # if not, raise an error
        raise AttributeError(f"Element has no attribute {item}!")
