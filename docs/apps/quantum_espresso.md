# Overview of Quantum Espresso App

--------------------------------------------------------------------------------

## About

Quantum ESPRESSO (QE) is widely used in computational chemistry and condensed matter physics to study the electronic structure of solids and molecules. It employs density functional theory (DFT) to calculate properties like electronic energy, charge density, and total energy. Researchers use it to gain insights into material properties at the quantum level.

It can be considered an alternative to popular DFT softwares such as VASP, CASTEP, and ABINIT.

Meanwhile, Simmate's QE app builds workflows and utilities on top of the QE code. Typically, other workflows oversee the execution of the workflows registered in this app.

--------------------------------------------------------------------------------

## Installation

1. Add `quantum_espresso` to the list of installed Simmate apps with:
``` bash
simmate config add quantum_espresso
```

2. Make sure you have Quantum Espresso (QE) installed using one of two options:
      - (*for beginners*) Install [Docker-Desktop](https://www.docker.com/products/docker-desktop/). Then run the following command:
          ``` bash
          simmate config update "quantum_espresso.docker.enable=True"
          ```
      - (*for experts*) Install QE using [offical guides](https://www.quantum-espresso.org/) and make sure `pw.x` is in the path

6. To run calculations with QE, we need psuedopotentials. Simmate helps load these from the popular [SSSP library](https://www.materialscloud.org/discover/sssp/):
``` bash
simmate-qe setup sssp
```

3. Update your database to include custom tables from the app:
``` shell
simmate database update
```

4. Ensure everything is configured correctly:
``` shell
simmate config test quantum_espresso
```

--------------------------------------------------------------------------------

## Helpful Resources

 - [Quantum Espresso website](https://www.quantum-espresso.org/) (includes documentation and guides)

--------------------------------------------------------------------------------
