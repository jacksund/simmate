#### b. Linux (Ubuntu)

1. Download the `Linux x86-64` version from the Henkelman website [here](http://theory.cm.utexas.edu/henkelman/code/bader/)
2. Unzip the downloaded file. It should contain a single executable named "bader".
3. Move the `bader` executable to a directory of your preference. For example, `~/bader/bader` (inside a folder named bader in my home directory)
4. Run `nano ~/.bashrc` to modify your bash and add this line at the end:
``` bash
export PATH=/home/jacksund/bader/:$PATH
```
1. Restart your terminal and test the command `bader --help`

*(optional)* `chgsum.pl` and additional scripts:

1. Download the scripts from [VTST-tools](http://theory.cm.utexas.edu/vtsttools/scripts.html)
2. Unzip the folder (`vtstscripts-1033`) and move it to the directory where your bader executable is located.
3. Run `nano ~/.bashrc` to modify your bash and add this line at the end:
``` bash
# Make sure to update the 'myname' part!
export PATH=/home/myname/bader/vtstscripts-1033:$PATH
```
4. Restart your terminal and confirm the bader command works