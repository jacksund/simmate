# The `Composition` Class

!!! note
    A `Composition` represents the "recipe" for a chemical. It tells you exactly which elements and how many atoms of each are present, but it does *not* include any information about where the atoms are located or how they are bonded.

----------------------------------------------------------------------

## Intro to the `Composition` class

In chemistry and materials science, we often describe a substance by its formula, such as `H2O`, `Ca2N`, or `NaCl`. In Simmate, these formulas are represented by the `Composition` class.

Let's load the `Composition` class:

```python
from simmate.toolkit import Composition
```

----------------------------------------------------------------------

## Creating Compositions

You can create a `Composition` object directly from a formula:

```python
water = Composition("H2O")
salt = Composition("NaCl")
```

----------------------------------------------------------------------

## Accessing Composition from Other Classes

The `Composition` class is actually a fundamental building block. Both the `Structure` and `Molecule` classes have a `composition` property that you can access!

```python
from simmate.toolkit import Structure, Molecule

# For crystals
nacl = Structure.from_file("POSCAR")
print(nacl.composition)

# For molecules
caffeine = Molecule.from_smiles("CN1C=NC2=C1C(=O)N(C(=O)N2C)C")
print(caffeine.composition)
```

----------------------------------------------------------------------

## Analyzing Compositions

Once you have a `Composition` object, you can access many useful properties:

**i: Elemental Breakdown**

```python
water.elements  # Returns (Element H, Element O)
water.get_el_amt("H")  # Returns 2.0
```

**ii: Formula Reductions**

```python
iron_oxide = Composition("Fe2O3")
iron_oxide.reduced_formula  # Returns "Fe2O3"

salt = Composition("Na4Cl4")
salt.reduced_formula  # Returns "NaCl"
```

**iii: Physical Estimates**

Simmate's `Composition` class can even estimate physical properties like density or volume, which is particularly useful when creating random structures:

```python
water.weight  # Atomic weight (approx 18.0)
water.volume_estimate()  # Predicted lattice volume
```

----------------------------------------------------------------------

## Comparison

Just like with molecules, compositions can be compared directly to check if two chemicals have the same elemental makeup:

```python
c1 = Composition("H2O")
c2 = Composition("H2O1")
print(c1 == c2)  # Returns True!
```

----------------------------------------------------------------------
