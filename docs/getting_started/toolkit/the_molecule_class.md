# The `Molecule` Class

!!! note
    While the `Structure` class focuses on crystals (repeating patterns), the `Molecule` class is for individual molecules.

----------------------------------------------------------------------

## Intro to the `Molecule` class

In chemistry, we often work with molecules like caffeine, aspirin, or water. In Simmate, these are represented by the `Molecule` class. 

Under the hood, Simmate uses [RDKit](https://www.rdkit.org/), but it provides a much simpler and more "Pythonic" interface for you to use.

Let's load the `Molecule` class:

```python
from simmate.toolkit import Molecule
```

----------------------------------------------------------------------

## Summary of Steps

Working with molecules follows a similar pattern to structures:

1. Loading a molecule into Python (usually from SMILES or SDF)
2. Cleaning or modifying the molecule
3. Analyzing properties (weight, rings, LogP, etc.)
4. Visualizing or exporting the molecule

----------------------------------------------------------------------

### 1. Load

The most common way to load a molecule is using a **SMILES string**, which is a text-based representation of a chemical structure.

Let's load **Aspirin**:

```python
aspirin = Molecule.from_smiles("CC(=O)OC1=CC=CC=C1C(=O)O")
```

To see the molecule you just loaded:

```python
print(aspirin)
```

!!! tip
    If you're using **Spyder** or **Jupyter**, you can simply type `aspirin` and hit enter. Simmate will automatically show you a 2D image of the molecule!

----------------------------------------------------------------------

### 2. Clean & Modify

Molecules often need 3D coordinates if you plan to run advanced simulations (like Quantum Espresso or VASP). By default, SMILES only gives you 2D connectivity.

**i: Generating 3D Coordinates**

You can "embed" the molecule to give it a rough 3D shape:

```python
aspirin.convert_to_3d()
```

**ii: Adding/Removing Hydrogens**

Many file formats omit hydrogens to save space. You can add them back:

```python
aspirin.add_hydrogens()
```

----------------------------------------------------------------------

### 3. Analyze

The `Molecule` class has dozens of properties ready for you to use.

**Basic properties:**

```python
aspirin.molecular_weight
aspirin.num_rings
aspirin.formula
aspirin.elements
```

**Advanced properties:**

Simmate also includes many predictors for common chemical properties:

```python
aspirin.log_p_rdkit  # Partition coefficient
aspirin.tpsa_rdkit   # Polar surface area
aspirin.synthetic_accessibility  # How hard is it to make? (1-10)
```

----------------------------------------------------------------------

### 4. Export

You can save your molecule to various formats. The most common is an **SDF file**, which stores the 3D coordinates and metadata.

```python
aspirin.to_sdf_file("aspirin.sdf")
```

You can also save it as an image:

```python
aspirin.to_png_file("aspirin.png")
```

----------------------------------------------------------------------

## Extra Tips & Tricks

### Viewing in Spyder

Just like with `Structure`, you can use Spyder's variable explorer to see your `Molecule` objects.

### Comparison

One of the best features of the `Molecule` class is that you can compare them directly. Simmate handles all the complex chemistry logic for you:

```python
mol1 = Molecule.from_smiles("C")
mol2 = Molecule.from_smiles("C")
print(mol1 == mol2)  # Returns True!
```

----------------------------------------------------------------------
