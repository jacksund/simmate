# BIOVIA COSMO

--------------------------------------------------------------------------------

## About

[BIOVIA COSMOtherm](https://www.3ds.com/products/biovia/cosmo-rs) predicts thermodynamic properties of molecules in solution using the COSMO-RS method. Simmate's `biovia_cosmo` app wraps two of its programs:

- **COSMOconf** for conformer generation (e.g. `conformer-generation.cosmo-conf.bp-svp-am1`)
- **COSMOtherm** for octanol-water partition coefficients (e.g. `solubility.biovia-cosmo.log-pow-bp-svp-am1`)

!!! warning
    A license is required to use the BIOVIA COSMO software.

--------------------------------------------------------------------------------

## Installation

1. Add `biovia_cosmo` to the list of installed Simmate apps with:
``` bash
simmate config add biovia_cosmo
```

2. Install COSMOconf and COSMOtherm and make sure the `cosmoconf.pl` and `cosmotherm` commands are in your path.

3. Place the COSMOtherm parameter files in `~/simmate/biovia_cosmo/`, with one folder per preset (e.g. `~/simmate/biovia_cosmo/BP_SVP_AM1_22`).

4. Update your database to include custom tables from the app:
``` shell
simmate database update
```

--------------------------------------------------------------------------------
