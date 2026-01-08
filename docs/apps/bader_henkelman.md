# Overview of Bader App

--------------------------------------------------------------------------------

## About

Bader Charge Analysis ("Bader" for short) is a technique for partitioning charge density to predict oxidation states. This module is specifically tailored for the [Henkelman Group](http://theory.cm.utexas.edu/henkelman/)'s code that performs this analysis. You can access their open-source code [here](http://theory.cm.utexas.edu/henkelman/code/bader/).

Meanwhile, Simmate's Bader app builds workflows and utilities on top of the Bader code from the Henkelman Lab. Typically, other workflows oversee the execution of the workflows registered in this app. For example, workflows in the `materials_project` app combine Bader, VASP, and rational settings. Hence, beginners are recommended to start with other apps.

--------------------------------------------------------------------------------

## Installation

1. Add `bader` to the list of installed Simmate apps with:
``` bash
simmate config add bader
```

2. Make sure you have the Bader command installed using one of two options:
      - (*for beginners*) Install [Docker-Desktop](https://www.docker.com/products/docker-desktop/). Then run the following command:
          ``` bash
          simmate config update "bader.docker.enable=True"
          ```
      - (*for experts*) Install Bader using [offical guides](http://theory.cm.utexas.edu/henkelman/code/bader/) and make sure `bader` is in the path

3. Ensure everything is configured correctly:
``` shell
simmate config test bader
```

--------------------------------------------------------------------------------

## Helpful Resources

 - [Bader Website](http://theory.cm.utexas.edu/henkelman/code/bader/) (includes documentation and guide)

--------------------------------------------------------------------------------
