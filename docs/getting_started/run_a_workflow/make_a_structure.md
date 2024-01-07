# Creating a Structure File

Before initiating a workflow, a crystal structure is required. There are numerous ways to obtain a crystal structure, such as downloading one online or creating one from scratch. In this guide, we will create a structure file from scratch without using any software.

----------------------------------------------------------------------

## Creating a Text (txt) File

Firstly, create a new text file on your Desktop named `POSCAR.txt`. You can use any text editor of your choice (Notepad, Sublime, etc.). Alternatively, you can create the file using the command line:

``` shell
nano POSCAR.txt
```

Ensure that the `.txt` extension is visible by enabling "show file name extensions".

Next, copy and paste the following text into the file:

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

This text represents a structure, which consists of a lattice and a list of atomic sites. The lattice is defined by a 3x3 matrix (lines 3-5), and the sites are a list of xyz coordinates with an element (lines 8-9 show fractional coordinates). 

----------------------------------------------------------------------

## Exploring a Different Format (cif)

There are various ways to write structure information. The example above uses the VASP's "POSCAR" format. Another common format is CIF. Although it's not as neat as a POSCAR, it contains similar information. You can use either CIFs or POSCAR formats when using Simmate.

``` cif
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

----------------------------------------------------------------------

## Understanding File Extensions

Most files you will interact with are text files, just in different formats. This is where file extensions come in (`.txt`, `.cif`, `.csv`, ...). 

These extensions indicate the format we are using. Files named `something.cif` inform programs that we have a text file written in the CIF structure format. 

VASP uses the name POSCAR (without any file extension) to indicate its format. If we rename our file from `POSCAR.txt` to `POSCAR`, all programs (VESTA, OVITO, and others) will recognize the structure. 

!!! note 
    In Windows, you may receive a warning about changing the file extension. You can safely ignore this warning and change the extension.

!!! Fun-fact
    A Microsoft Word document is essentially a folder of text files. The .docx file extension tells Word that we have the folder in their desired format. Try renaming a word file from `my_file.docx` to `my_file.zip` and open it to explore. Most programs operate in a similar manner!

----------------------------------------------------------------------

## Renaming Your File in the Command-Line

If you're using the command-line to create/edit this file, you can use the copy (`cp`) command to rename your `POSCAR.txt` file to `POSCAR`:

``` shell
cp POSCAR.txt POSCAR
```

Your structure file is now ready to use!

----------------------------------------------------------------------