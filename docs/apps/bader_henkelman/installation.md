
# Installation (Ubuntu 22.04)

Both sections are required for use of Simmate workflows.

**For the `bader` command:**

1. Download `Linux x86-64` from the Henkelman website [here](http://theory.cm.utexas.edu/henkelman/code/bader/)
2. Unpack the compressed file. There should only be one "file" in it named bader. This is the executable.
3. Move the `bader` executable to a folder of your choosing. For example, `~/jacksund/bader/bader` (within a folder named bader in my home directory)
4. run `nano ~/.bashrc` to edit your bash and add this line to the bottom:
``` bash
export PATH=/home/jacksund/bader/:$PATH
```
5. restart your terminal and try the command `bader --help`

**For the `chgsum.pl` and extra scripts:**

1. Download the scripts from [VTST-tools](http://theory.cm.utexas.edu/vtsttools/scripts.html)
2. Unpack the folder (`vtstscripts-1033`) and move it into the folder with your bader executable
3. run `nano ~/.bashrc` to edit your bash and add this line to the bottom:
``` bash
export PATH=/home/jacksund/bader/vtstscripts-1033:$PATH
```
4. restart your terminal and you're ready to try Bader analyses with Simmate!
