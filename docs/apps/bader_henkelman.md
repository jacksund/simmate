# Overview of Bader App

## Introduction to Bader

Bader Charge Analysis, often known as "Bader", is a technique for partitioning charge density to forecast oxidation states. This module is specifically tailored for the [Henkelman Group](http://theory.cm.utexas.edu/henkelman/)'s code that performs this analysis.

You can access the open-source code [here](http://theory.cm.utexas.edu/henkelman/code/bader/).

## About the Bader App

The Bader app utilizes Simmate tools to build workflows and utilities based on the Bader code from the Henkelman Lab. 

Typically, other workflows oversee the execution of the workflows registered in this app. For example, workflows in the `Warren Lab` app combine Bader, VASP, and rational settings. Hence, beginners are recommended to start with other apps.

## Installation Guide (Ubuntu 22.04)

### Installing the `bader` command

1. Download the `Linux x86-64` version from the Henkelman website [here](http://theory.cm.utexas.edu/henkelman/code/bader/)
2. Unzip the downloaded file. It should contain a single executable named "bader".
3. Move the `bader` executable to a directory of your preference. For example, `~/jacksund/bader/bader` (inside a folder named bader in my home directory)
4. Run `nano ~/.bashrc` to modify your bash and add this line at the end:
``` bash
export PATH=/home/jacksund/bader/:$PATH
```
5. Restart your terminal and test the command `bader --help`

### Installing `chgsum.pl` and additional scripts

1. Download the scripts from [VTST-tools](http://theory.cm.utexas.edu/vtsttools/scripts.html)
2. Unzip the folder (`vtstscripts-1033`) and move it to the directory where your bader executable is located.
3. Run `nano ~/.bashrc` to modify your bash and add this line at the end:
``` bash
export PATH=/home/jacksund/bader/vtstscripts-1033:$PATH
```
4. Restart your terminal and you're ready to perform Bader analyses with Simmate!

## Useful Resources

 - [Bader Website](http://theory.cm.utexas.edu/henkelman/code/bader/) (includes documentation and guide)