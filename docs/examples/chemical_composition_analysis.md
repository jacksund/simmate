
# Chemical Composition Analysis

## About :star:

This script demonstrates how to work with chemical compositions in Simmate. We show how to create a `Composition` object from a string, calculate its formula weight, find the weight percentages of its elements, and get a guess for its oxidation states.

| Key Info        |                                            |
| --------------- | ------------------------------------------ |
| Contributor     | Simmate Team                               |
| Last updated    | 2026.03.14                                 |
| Level           | **Beginner**                               |

## Prerequisites :rotating_light:

*No extra configuration is required for this script.*

## The script :rocket:

``` python
from simmate.toolkit import Composition

# 1. Create a composition object
# You can use standard chemical formulas.
comp = Composition("LiFePO4")

# 2. Get basic properties
print(f"Reduced Formula: {comp.reduced_formula}")
print(f"Weight: {comp.weight:.2f} g/mol")
print(f"Total elements: {len(comp.elements)}")

# 3. Get element percentages (by weight)
# We can find out how much of the formula is made up of each element.
for element in comp.elements:
    pct = comp.get_wt_percentage(element)
    print(f"{element.symbol}: {pct*100:.2f}% by weight")

# 4. Guess oxidation states
# This uses a simple bond-valence sum approach to guess the oxidation 
# states of the elements.
try:
    ox_states = comp.oxi_state_guesses()
    print(f"Guessed oxidation states: {ox_states}")
except:
    print("Unable to guess oxidation states for this composition.")

# 5. Advanced: Check the chemical system
# You can get a string of elements sorted alphabetically.
print(f"Chemical System: {comp.chemical_system}")

# And find all unique sub-systems (e.g. Li-Fe, Li-O, etc.)
subsystems = comp.chemical_subsystems
print(f"Found {len(subsystems)} sub-systems")
```
