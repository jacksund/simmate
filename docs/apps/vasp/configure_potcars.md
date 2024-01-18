# Setting Up Potentials (for VASP users)

----------------------------------------------------------------------

## What is VASP?

VASP is a widely used software for executing DFT calculations. However, our team cannot install it for you due to its commercial licensing. You need to [acquire it directly from the VASP team](https://www.vasp.at/), with whom we have no affiliation. 

----------------------------------------------------------------------

## Setting Up VASP

Even though VASP can only be installed on Linux, we will guide you through the process of configuring VASP on your local computer, regardless of whether it's a Windows or Mac system. For this, you only need the Potentials that come with the VASP installation files. You can either:

1. Extract these from the VASP installation files located at `vasp/5.x.x/dist/Potentials`. Remember to unpack the `tar.gz` files.
2. Request a copy of these files from a team member or your IT department.

After obtaining the potentials, place them in a folder named `~/simmate/vasp/Potentials`. This is the same directory where your database is located (`~/simmate`). Here, you need to create a new folder named `vasp`. This folder should contain the potentials that came with VASP, maintaining their original folder and file names. Once you've completed these steps, your folder should look like this:

```
# Located at /home/my_username (~)
simmate/
├── my_env-database.sqlite3
└── vasp
    └── Potentials
        ├── LDA
        │   ├── potpaw_LDA
        │   ├── potpaw_LDA.52
        │   ├── potpaw_LDA.54
        │   └── potUSPP_LDA
        ├── PBE
        │   ├── potpaw_PBE
        │   ├── potpaw_PBE.52
        │   └── potpaw_PBE.54
        └── PW91
            ├── potpaw_GGA
            └── potUSPP_GGA
```

----------------------------------------------------------------------

## Verifying Your Configuration

If the folder is not set up correctly, subsequent commands may fail, resulting in an error like this:

``` python
FileNotFoundError: [Errno 2] No such file or directory: '/home/jacksund/simmate/vasp/Potentials/PBE/potpaw_PBE.54/Na/POTCAR'
```

If you encounter this error, revisit your folder setup.

!!! danger 
    Our team only has access to VASP v5.4.4. If your folder structure differs for newer versions of VASP, please inform us by [opening an issue](https://github.com/jacksund/simmate/issues).

----------------------------------------------------------------------