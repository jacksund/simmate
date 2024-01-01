# -*- coding: utf-8 -*-

from .pwscf_xml import PwscfXml

# -----------------------------------------------------------------------------

# DEV NOTES:

# -- pwscf.out --
# This file is not read or parsed anywhere
# This is because the `pwscf.out` file contains minimal information & not all
# of it is in a machine readable format. All information (and more) is in
# the `pwscf.xml` file instead, which we use instead.
# If we ever want to parse the out file instead, we can fork pymatgen's parser:
#   https://github.com/materialsproject/pymatgen/blob/master/pymatgen/io/pwscf.py


# -- pwscf.save/*.dat files -- (e.g. charge-density.dat)
# These files are in binary format and can only be read on the OS they were
# created/written on. This causes trouble for file sharing... Ideally we can
# convert these to XML (using FoX) before trying to read. Otherwise, binary
# files can be loaded using h5py.
#   https://github.com/QEF/qeschema/blob/master/qeschema/hdf5/__init__.py#L15

# -----------------------------------------------------------------------------
