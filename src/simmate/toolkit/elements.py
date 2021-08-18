# -*- coding: utf-8 -*-

from enum import Enum

from simmate.materials_science.element_data import ALL_DATA, SUPPORTED_PROPERTIES


class Element(Enum):
    """
    The Element class is really just a dictionary of fixed data, but we perform some
    extra python "tricks" to help with performance and usage.

    WARNING: This class implements some advanced python topics, and you don't need
    to understand them to use this class as a beginner. Check out element_data.py
    (and the csv file) to see which data is available. Also look at this link for a
    quick tutorial:
        << TODO: INSERT LINK >>

    The main performance boost comes from making this a subclass of Enum, which
    means there are fixed number of options to choose from. Further, once one is
    chosen, it never changes. This means we really only need one object instance
    for each element -- and any time we call Element("Al"), it will share that instance
    and data. This is effectively a "singleton" and helps us save on memory and
    object initialization in a big way.

    The second thing we do is "lazy-loading" of an Element's attributes. This helps
    with how fast we can create Element objects. In 99% of cases, we really don't need
    all of the data for an element -- just the symbol. Therefore, data isn't loaded
    and attached to Element objects until they need to be. Once you call that attribute,
    we then link it to the object and it's there for good. This helps with performance
    too because once an attribute is accessed, it will likely be accessed again.
    """

    # These are the only possible Elements. Any other inputs for this class will
    # raise an error. Note, we also include a dummy element for when a site needs
    # to be specified without assigning an element to it: this is Unknown = "X"
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
    Unknown = "X"

    def __init__(self, symbol):

        self.symbol = symbol

        # OPTIMIZE: consider adding key attributes here for speed. The cost of
        # adding upfront is ___ns while adding later costs ___ns
        # I could have an enviornment variable so users can set this directly too.
        # That would be advanced usage, but may be useful to some.
        # For example...
        # self.atomic_number = ALL_DATA[symbol]["atomic_number"]

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
        this is also wasted overhead.
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

    def __str__(self):
        """Just return the symbol if we want the Element as a String"""
        return self.symbol

    def __lt__(self, other):
        """
        Establishes how we evalutate "Element1 < Element2".

        This allows us to sort atomic species by electronegativity and then
        by symbol for equal electronegativities. Very useful for getting correct
        formulas. For example, FeO4PLi is automatically sorted into LiFePO4.
        """
        # NOTE: list sorting only uses less-than comparisons, so we don't need to
        # define a __gt__ method.

        # Not all elements have electronegativities, so we grab them first. If
        # an element doesn't have one, we set it to infinity. Otherwise, an
        # error will be thrown if we compare None with a float.
        x1 = self.electronegativity if self.electronegativity else float("inf")
        x2 = other.electronegativity if other.electronegativity else float("inf")

        # if the electronegativities are not equal, return whether the "other"
        # is less-than or not.
        if x1 != x2:
            return x1 < x2
        # If electronegativities are equal, we then sort alphabetically by symbol.
        else:
            return self.symbol < other.symbol

    @staticmethod
    def from_atomic_number(atomic_number):
        """Returns an element from an atomic number."""

        # iterate through each element until we find the one where numbers match
        for symbol, data in ALL_DATA.items():
            if data["atomic_number"] == atomic_number:
                return Element(symbol)

        # if we never find a match, raise an error
        raise ValueError(f"No element with atomic number {atomic_number}")

    @staticmethod
    def from_row_and_group(row_number, group_number):
        """
        Returns an element from a row and group number.
        Note that the 18 group number system is used, i.e., Noble gases are group 18.
        """

        # iterate through each element until we find the one where numbers match
        for symbol, data in ALL_DATA.items():
            if (
                data["row_number"] == row_number
                and data["group_number"] == group_number
            ):
                return Element(symbol)

        # if we never find a match, raise an error
        raise ValueError(f"No element with row {row_number} and group {group_number}")

    def all_data(self):
        """Returns the full dictionary of data available for the element"""
        return ALL_DATA[self.symbol]

    # OPTIMIZE: consider changing these properties to check group/row numbers instead
    # of comparing lists. For example, noble gases would check "group_number == 18".

    @property
    def is_noble_gas(self):
        """True if element is noble gas."""
        noble_gases = (2, 10, 18, 36, 54, 86, 118)
        return self.atomic_number in noble_gases

    @property
    def is_transition_metal(self):
        """True if element is a transition metal."""
        transition_metals = (
            list(range(21, 31))
            + [57]
            + list(range(72, 81))
            + [89]
            + list(range(104, 113))
        )
        return self.atomic_number in transition_metals

    @property
    def is_post_transition_metal(self):
        """True if element is a post-transition or poor metal."""
        post_transition_metals = (13, 31, 49, 50, 81, 82, 83)
        return self.atomic_number in post_transition_metals

    @property
    def is_metalloid(self):
        """True if element is a metalloid."""
        metalloids = (5, 14, 32, 33, 51, 52, 84)
        return self.atomic_number in metalloids

    @property
    def is_alkali(self):
        """True if element is an alkali metal."""
        alkali_metals = (3, 11, 19, 37, 55, 87)
        return self.atomic_number in alkali_metals

    @property
    def is_alkaline(self):
        """True if element is an alkaline earth metal"""
        alkali_earth_metals = (4, 12, 20, 38, 56, 88)
        return self.atomic_number in alkali_earth_metals

    @property
    def is_halogen(self):
        """True if element is a halogen."""
        halogens = (9, 17, 35, 53, 85)
        return self.atomic_number in halogens

    @property
    def is_chalcogen(self):
        """True if element is a chalcogen."""
        chalcogens = (8, 16, 34, 52, 84)
        return self.atomic_number in chalcogens

    @property
    def is_lanthanoid(self):
        """True if element is a lanthanoid."""
        return 56 < self.atomic_number < 72

    @property
    def is_actinoid(self):
        """True if element is a actinoid."""
        return 88 < self.atomic_number < 104

    @property
    def is_rare_earth_metal(self):
        """True if element is a rare earth metal."""
        return self.is_lanthanoid or self.is_actinoid

    @property
    def is_metal(self):
        """True if element is a metal."""
        # if any of these are true, it's a metal
        return (
            self.is_alkali
            or self.is_alkaline
            or self.is_post_transition_metal
            or self.is_transition_metal
            or self.is_lanthanoid
            or self.is_actinoid
        )

    @property
    def is_quadrupolar(self):
        """Checks if this element can be quadrupolar"""
        # If the element has nmr_quadrupole_moment data, it can be quadrupolar.
        # Otherwise it is not. We use bool() return true/false
        return bool(self.nmr_quadrupole_moment)
