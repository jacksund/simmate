
# Making a structure file

Before we run a workflow, we need a crystal structure to run it on. There are many ways to get a crystal structure -- such as downloading one online or using a program to create one from scratch. Here, in order to learn about structure files, we are going to make one from scratch without any program.

First, make a new text file on your Desktop named `POSCAR.txt`. You can use which text editor you prefer (Notepad, Sublime, etc.). You can also create the file using the command like with:

``` shell
nano POSCAR.txt
```

Note, we can see the `.txt` ending because we enabled "show file name extensions" above.

Once you have this file, copy/paste this text into it:

```
Na1 Cl1
1.0
3.485437 0.000000 2.012318
1.161812 3.286101 2.012318
0.000000 0.000000 4.024635
Na Cl
1 1
direct
0.000000 0.000000 0.000000 Na
0.500000 0.500000 0.500000 Cl
```

This text is everything we need to represent a structure, which is just a lattice and a list of atomic sites. The lattice is defined by a 3x3 matrix (lines 3-5) and the sites are just a list of xyz coordinates with an element (lines 8-9 show fractional coordinates). There are many different ways to write this information; here we are using the VASP's POSCAR format. Another popular format is CIF. It's not as clean and tidy as a POSCAR, but it holds similar information:
```
data_NaCl
_symmetry_space_group_name_H-M   'P 1'
_cell_length_a   4.02463542
_cell_length_b   4.02463542
_cell_length_c   4.02463542
_cell_angle_alpha   60.00000000
_cell_angle_beta   60.00000000
_cell_angle_gamma   60.00000000
_symmetry_Int_Tables_number   1
_chemical_formula_structural   NaCl
_chemical_formula_sum   'Na1 Cl1'
_cell_volume   46.09614833
_cell_formula_units_Z   1
loop_
 _symmetry_equiv_pos_site_id
 _symmetry_equiv_pos_as_xyz
  1  'x, y, z'
loop_
 _atom_site_type_symbol
 _atom_site_label
 _atom_site_symmetry_multiplicity
 _atom_site_fract_x
 _atom_site_fract_y
 _atom_site_fract_z
 _atom_site_occupancy
  Na  Na0  1  0.00000000  0.00000000  0.00000000  1
  Cl  Cl1  1  0.50000000  0.50000000  0.50000000  1
```

Nearly all files that you will interact with are text files -- just in different formats. That's where file extensions come in. They indicate what format we are using. Files named `something.cif` just tell programs we have a text file written in the CIF structure format. VASP uses the name POSCAR (without any file extension) to show its format. So rename your file from `POSCAR.txt` to `POSCAR`, and now all programs (VESTA, OVITO, and others) will know what to do with your structure. In Windows, you will often receive a warning about changing the file extension. Ignore the warning and change the extension.

If you're using the command-line to create/edit this file, you can use the copy (`cp`) command to make the `POSCAR` file:

``` shell
cp POSCAR.txt POSCAR
```

We now have our structure ready to go!

!!! Fun-fact
    a Microsoft Word document is just a folder of text files. The .docx file ending tells Word that we have the folder in their desired format. Try renaming a word file from `my_file.docx` to `my_file.zip` and open it up to explore. Nearly all programs do something like this!

