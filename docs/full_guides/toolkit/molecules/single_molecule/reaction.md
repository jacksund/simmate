# Reaction Class

--------------------------------------------------------------------------------

## Introduction

The `Reaction` class handles chemical reactions involving multiple `Molecule` objects. It simplifies tasks like reaction visualization, transformation from strings, and applying reaction templates to specific reactants.

--------------------------------------------------------------------------------

## Loading Reactions

The easiest way to load a reaction is from a SMILES or SMARTS string using the `from_smiles` method.

``` python
from simmate.toolkit import Reaction

# Standard reactant > reagent > product SMILES
smiles = "CC(=O)O.OCC>S(=O)(=O)(O)O>CC(=O)OCC.O"
reaction = Reaction.from_smiles(smiles)

# You can also use SMARTS for general reaction templates
template = "[C:1](=[O:2])-[OD1].[O:3]-[C:4]>>[C:1](=[O:2])-[O:3]-[C:4]"
reaction = Reaction.from_smarts(template)
```

--------------------------------------------------------------------------------

## Visualization

Simmate can generate high-quality images for reactions, making them easy to view in an interactive environment or export for a publication.

``` python
# Returns an image for interactive display
img = reaction.image

# Export as a PNG file
reaction.to_png_file("my_reaction.png")
```

--------------------------------------------------------------------------------

## Reaction Templates

Simmate supports reaction templates that can be applied to specific reactants to predict products.

``` python
# Create a general reaction template
template = Reaction.from_smarts("[C:1](=[O:2])-[OD1].[O:3]-[C:4]>>[C:1](=[O:2])-[O:3]-[C:4]")

# Apply the template to specific molecules
from simmate.toolkit import Molecule
reactants = [
    Molecule.from_smiles("CC(=O)O"), 
    Molecule.from_smiles("CO")
]
products = template.apply_template(reactants)

# View the results
for product in products:
    print(product.to_smiles())
```

--------------------------------------------------------------------------------
