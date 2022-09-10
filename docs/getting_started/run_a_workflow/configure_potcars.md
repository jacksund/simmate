
# Configuring Potentials (for VASP users)

!!! warning
    once Simmate switches from VASP to a free DFT alternative, this section of the tutorial will be optional and removed.

----------------------------------------------------------------------

## What is VASP?

VASP is a very popular software for running DFT calculations, but our team can't install it for you because VASP is commercially licensed (i.e. you need to [purchase it from their team](https://www.vasp.at/), which we are not affiliated with). 

Simmate is working to switch to another DFT software -- specifically one that is free/open-source, that can be preinstalled for you, and that you can use on Windows+Mac+Linux. Until Simmate reaches this milestone, you'll have to use VASP. We apologize for the inconvenience.

----------------------------------------------------------------------

## Configuring VASP

While VASP can only be installed on Linux, we will still practice configuring VASP on our local computer -- even if it's Windows or Mac. To do this, you only need the Potentials that are distrubited with the VASP installation files. You can either...

1. Grab these from the VASP installation files. You can find them at `vasp/5.x.x/dist/Potentials`. Be sure to unpack the `tar.gz` files.
2. Ask a team member or your IT team for a copy of these files.

Once you have the potentials, paste them into a folder named `~/simmate/vasp/Potentials`. Note, this is same directory that your database is in (`~/simmate`) where you need to make a new folder named `vasp`. This folder will have the potentials that came with VASP -- and with their original folder+file names. Once you have all of this done, you're folder should look like this:

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

## Checking your configuration

If you made this folder incorrectly, commands that you use later will fail with an error like...

``` python
FileNotFoundError: [Errno 2] No such file or directory: '/home/jacksund/simmate/vasp/Potentials/PBE/potpaw_PBE.54/Na/POTCAR'
```

If you see this error, double-check your folder setup.

!!! danger 
    our team only has access to VASP v5.4.4, so if your folder structure differs for newer versions of VASP, please let our know by [opening an issue](https://github.com/jacksund/simmate/issues).

----------------------------------------------------------------------
