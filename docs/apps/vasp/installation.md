# VASP App Installation

## Installation

1. Add `vasp` (and it's dependencies) to the list of installed Simmate apps with:
``` bash
simmate config add vasp
```

2. Make sure you have the `vasp_std` command installed using one of two options:
      - (*for beginners*) Install [Docker-Desktop](https://www.docker.com/products/docker-desktop/). Then run the following commands:
          ``` bash
          simmate config update "vasp.docker.enable=True"
          simmate config update "vasp.docker.image=example.com:vasp/latest"
          ```

        !!! danger
            VASP is a commercial software, so we cannot provide Docker images for it. This is why you must provide a private image via `image=example.com:vasp/latest`.

      - (*for experts*) Install VASP using [offical guides](https://www.vasp.at/) and make sure `vasp_std` is in the path

3. Configure VASP POTCAR files. You can either extract these from the VASP installation files located at `vasp/5.x.x/dist/Potentials` or request a copy of these files from a team member or your IT department. Unpack the `tar.gz` files and place them in `~/simmate/vasp/Potentials`, maintaining their original folder and file names. Once you've completed these steps, your folder should look like this:
```
# Located at /home/my_username (~)
simmate/
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

    !!! note
        If the folder is not set up correctly, subsequent commands may fail, resulting in an error like this:

        ``` python
        FileNotFoundError: [Errno 2] No such file or directory: '/home/jacksund/simmate/vasp/Potentials/PBE/potpaw_PBE.54/Na/POTCAR'
        ```

        If you encounter this error, revisit your folder setup.

    !!! danger 
        Our team only has access to VASP v5.4.4. If your folder structure differs for newer versions of VASP, please inform us by [opening an issue](https://github.com/jacksund/simmate/issues).


4. Ensure everything is configured correctly:
``` shell
simmate config test vasp
```
