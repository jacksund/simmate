# OpenEye OMEGA

--------------------------------------------------------------------------------

## About

[OpenEye OMEGA](https://www.eyesopen.com/omega) generates 3D conformers for molecules. Simmate's `openeye_omega` app provides a base `OmegaWorkflow` for running OMEGA with custom parameters, along with a preset that prepares conformers for FastROCS (`conformer-generation.openeye-omega.fastrocs-prep`).

!!! warning
    A license is required to use the OpenEye software.

--------------------------------------------------------------------------------

## Installation

1. Add `openeye_omega` to the list of installed Simmate apps with:
``` bash
simmate config add openeye_omega
```

2. Install OMEGA and make sure the `oeomega` command is in your path.

--------------------------------------------------------------------------------
