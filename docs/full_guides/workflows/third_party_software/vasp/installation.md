# VASP Installation

Official guides can be found on the VASP wiki [here](https://www.vasp.at/wiki/index.php/Installing_VASP.6.X.X). For example, there are clear [guides](https://www.vasp.at/wiki/index.php/Personal_computer_installation) for installing VASP onto your personal computer, such as VASP 6 on Ubuntu 22.04.


## VASP 5.4.4 on Ubuntu 22.04

This guide is specifically for the Warren Lab as it requires build files that we share within the team. 

To guarantee compatibility, we need to build all vasp dependencies by hand (for example, Ubuntu uses gcc v11 but vasp requires v9). For the Warren Lab, we have packaged everything in one zip file to make setup as simple as possible. Copy /media/synology/software/vasp/vasp.zip from WarWulf to your computer, such as your home directory (e.g. `/home/jacksund/`). This file is only 172.1MB, but will be over 9GB once we are finished installing vasp.

Within the vasp directory, there are folders from (1) to (9) for each build step. These are the 9 programs that need to be built from source. Source files (*.tar.gz) are provided in each directory. Each folder also contains an "install" directory where the program will be installed. You'll also find another folder (usually the program name) that contains the unzipped contents of the *.tar.gz.

Make sure the necessary build tools are installed and up to date:
``` bash
sudo apt update
sudo apt upgrade
sudo apt install gcc make m4 g++ gfortran
``` 

1. install `gmp`

``` bash
# NOTE: steps are effectively the same with other programs but
# we only include comments on this first install

# open the folder for the step we are on
cd ~/vasp/01_gmp

# unzip our build files
tar xvzf *.tar.gz

# switch into the directory before performing the rest of install steps
cd gmp-6.2.1

# update this command with the proper path + username
./configure --prefix=/home/jacksund/vasp/01_gmp/install

# PAUSE AND READ OUTPUT OF THIS COMMAND
# Look for "Thread(s) per core and use" this in the next command
lscpu

# “2” here is based on our output from the previous command. This value will 
# be used in building our other packages too 
make -j 2
make install
make check # (optional) to confirm successful install
```

2. install `mpfr`
``` bash
cd ~/vasp/02_mpfr
tar xvzf *.tar.gz
cd mpfr-4.1.0
./configure --prefix=/home/jacksund/vasp/02_mpfr/install --with-gmp=/home/jacksund/vasp/01_gmp/install
make -j 2
make install
make check
```

3. install `mpc` 
``` bash
cd ~/vasp/03_mpc
tar xvzf *.tar.gz
cd mpc-1.2.1
./configure --prefix=/home/jacksund/vasp/03_mpc/install --with-gmp=/home/jacksund/vasp/01_gmp/install --with-mpfr=/home/jacksund/vasp/02_mpfr/install
make -j 2
make install
make check
```
 
4. install `gcc`
``` bash
cd ~/vasp/04_gcc
tar xvzf *.tar.gz
cd gcc-9.5.0
mkdir build
cd build
../configure --prefix=/home/jacksund/vasp/04_gcc/install --with-gmp=/home/jacksund/vasp/01_gmp/install --with-mpfr=/home/jacksund/vasp/02_mpfr/install --with-mpc=/home/jacksund/vasp/03_mpc/install --disable-multilib
make -j 2  # this command takes roughly 1hr
make install

nano ~/.bashrc
# ADD TO BOTTOM OF FILE
#
# export PATH=/home/jacksund/vasp/04_gcc/install/bin:$PATH
# export LD_LIBRARY_PATH=/home/jacksund/vasp/04_gcc/install/lib64:$LD_LIBRARY_PATH

source ~/.bashrc
```

5. install `openmpi`
``` bash
cd ~/vasp/05_openmpi
tar xvzf *.tar.gz
cd openmpi-4.1.4
mkdir build
cd build
../configure --prefix=/home/jacksund/vasp/05_openmpi/install
make -j 2
make install

nano ~/.bashrc
# ADD TO BOTTOM OF FILE
#
# export PATH=/home/jacksund/vasp/05_openmpi/install/bin:$PATH
# export LD_LIBRARY_PATH=/vasp/05_openmpi/install/lib:$LD_LIBRARY_PATH

source ~/.bashrc
mpirun --help
```

6. install `fftw`
``` bash
cd ~/vasp/06_fftw
tar xvzf *.tar.gz
cd fftw-3.3.10
mkdir build
cd build
../configure --prefix=/home/jacksund/vasp/06_fftw/install
make -j 2
make install ### Scott didn’t include this command. Typo?

nano ~/.bashrc
# ADD TO BOTTOM OF FILE
#
# export PATH=/home/jacksund/vasp/06_fftw/install/bin:$PATH

source ~/.bashrc
```

7. install `lapack` (blas, cblas, lapacke, lapack)
``` bash
cd ~/vasp/07_lapack
tar xvzf *.tar.gz
cd lapack-3.10.1
mv make.inc.example make.inc
make all
mkdir /home/jacksund/vasp/07_lapack/install
cp *.a /home/jacksund/vasp/07_lapack/install
cd ../install
cp librefblas.a libblas.a
```

8. install `scalapack`
``` bash
cd ~/vasp/08_scalapack
tar xvzf *.tar.gz
cd scalapack-2.2.0
mv SLmake.inc.example SLmake.inc

nano SLmake.inc
# Edit these lines: (leave then uncommented)
#
# BLASLIB = -L/home/jacksund/vasp/07_lapack/install -lblas
# LAPACKLIB = -L/home/jacksund/vasp/07_lapack/install -llapack
# LIBS = $(LAPACKLIB) $(BLASLIB)

make all
cp libscalapack.a ../../07_lapack/install
```

9. install `vasp`
``` bash
cd ~/vasp/09_vasp

nano makefile.include
# Edit these lines: (leave then uncommented)
#
# LIBDIR     = /home/jacksund/vasp/07_lapack/install/
# FFTW       ?= /home/jacksund/vasp/06_fftw/install

make std

nano ~/.bashrc
# ADD TO BOTTOM OF FILE
#
# export PATH=/home/jacksund/vasp/09_vasp/bin/:$PATH

source ~/.bashrc
```

You can now use commands like `mpirun -n 4 vasp_std`!!! If you try this right away, you’ll see the “error” (vasp fails because no input files are present)..
``` bash
Error reading item 'VCAIMAGES' from file INCAR.
Error reading item 'VCAIMAGES' from file INCAR.
Error reading item 'VCAIMAGES' from file INCAR.
Error reading item 'VCAIMAGES' from file INCAR.
```
