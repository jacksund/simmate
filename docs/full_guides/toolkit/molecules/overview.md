# Toolkit Overview

--------------------------------------------------------------------------------

## About

The `Simmate Toolkit` serves as an alternative to `RDkit`, `OpenEye-Toolkit`, and other Python packages for cheminformatics.

Our toolkit is the product of...

- [x] Incorporating features from other toolkits (e.g., wrapping an RDkit function)
- [x] Creating more Pythonic and user-friendly APIs
- [x] Adding optional integrations with databases and workflows 

Our toolkit is "batteries-included", meaning it includes many features typically used in large projects. As a result, it requires a larger installation (i.e., more dependencies). However, this also means that larger projects can benefit significantly from using our toolkit instead of building features from scratch with toolkits like RDkit.

--------------------------------------------------------------------------------

## :sparkles: Preview :sparkles:

To understand how the Simmate Toolkit simplifies tasks, consider this script. The script...

1.  Reads an SDF file containing multiple molecules
2.  Removes all molecules with more than 3 stereocenters, more than 30 heavy atoms, and containing sodium (`Na`)
3.  Generates a list of InChI keys from the final set

This script is less intuitive and less Pythonic for other toolkits, but it's straightforward and clean with Simmate:

=== "simmate-toolkit"
    ``` python
    from simmate.toolkit import Molecule

    # STEP 1
    molecules = Molecule.from_sdf_file("example.sdf")

    # STEP 2
    molecules_filtered = []
    for molecule in molecules:
        if molecule.num_stereocenters > 3:
            continue
        if molecule.num_atoms_heavy > 30:
            continue
        if "Na" in molecule.elements:
            continue
        molecules_filtered.append(molecule)

    # STEP 3
    inchi_keys = [m.to_inchi_key() for m in molecules_filtered]
    ```

=== "rdkit"
    ``` python
    from rdkit import Chem
    from rdkit.Chem import FindMolChiralCenters, Descriptors

    # STEP 1
    molecules = []
    with Chem.SDMolSupplier("example.sdf") as supplier:
    for molecule in supplier:
        if mol is None:
            continue
        molecules.append(molecule)

    # STEP 2
    molecules_filtered = []
    for molecule in molecules:

        chiral_centers = FindMolChiralCenters(
            molecule,
            force=True,
            includeUnassigned=True,
            useLegacyImplementation=False,
        )
        if len(chiral_centers) > 3:
            continue
        
        nheavy = Descriptors.HeavyAtomCount(molecule)
        if nheavy > 30:
            continue

        has_na = False  # false until proven otherwise
        for atom in molecule.GetAtoms():
            if atom.GetSymbol() == "Na":
                has_na = True
                break
        if has_na:
            continue

        molecules_filtered.append(molecule)

    # STEP 3
    inchi_keys = [Chem.MolToInchiKey(m) for m in molecules_filtered]
    ```

=== "oe-toolkit"
    ``` python
    from openeye import oechem
    from openeye import oeiupac
    
    # STEP 1
    molecules = []
    with oechem.oemolistream("example.sdf") as ifs:
        for mol in ifs.GetOEMols():
            if mol is None:
                continue
            molecules.append(mol)
    
    # STEP 2
    molecules_filtered = []
    for mol in molecules:
    
        stereo_count = sum(1 for atom in mol.GetAtoms() if atom.IsChiral())
        if stereo_count > 3:
            continue
    
        heavy_atom_count = sum(
            1 for atom in mol.GetAtoms() if atom.GetAtomicNum() > 1
        )
        if heavy_atom_count > 30:
            continue
    
        has_na = any(atom.GetAtomicNum() == 11 for atom in mol.GetAtoms())
        if has_na:
            continue
    
        molecules_filtered.append(mol)
    
    # STEP 3
    inchi_keys = [oeiupac.OECreateInChIKey(m) for m in molecules_filtered]
    ```

--------------------------------------------------------------------------------