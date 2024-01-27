# VASP Installation

You can find the official guides on the VASP wiki [here](https://www.vasp.at/wiki/index.php/Installing_VASP.6.X.X). This includes detailed [guides](https://www.vasp.at/wiki/index.php/Personal_computer_installation) for installing VASP on your personal computer, such as VASP 6 on Ubuntu 22.04.

## VASP 5.4.4 on Ubuntu 22.04

This guide is tailored for the Warren Lab as it requires specific build files shared within the team.

To ensure compatibility, we need to manually build all VASP dependencies (for instance, Ubuntu uses gcc v11 but VASP requires v9). For the Warren Lab, we have bundled everything into a single zip file to simplify the setup process. Copy /media/synology/software/vasp/vasp.zip from WarWulf to your computer, for example, your home directory (e.g. `/home/jacksund/`). This file is only 172.1MB, but will expand to over 9GB once VASP is fully installed.

The VASP directory contains folders (1) to (9) for each build step. These are the 9 programs that need to be built from source. Source files (*.tar.gz) are provided in each directory. Each folder also contains an "install" directory where the program will be installed. You'll also find another folder (usually the program name) that contains the unzipped contents of the *.tar.gz.

Ensure the necessary build tools are installed and up to date:
``` bash
sudo apt update
sudo apt upgrade
sudo apt install gcc make m4 g++ gfortran
``` 

1. Install `gmp`

``` bash
cd ~/vasp/01_gmp
tar xvzf *.tar.gz
cd gmp-6.2.1
./configure --prefix=/home/jacksund/vasp/01_gmp/install
lscpu
make -j 2
make install
make check # (optional) to confirm successful install
```

2. Install `mpfr`
``` bash
cd ~/vasp/02_mpfr
tar xvzf *.tar.gz
cd mpfr-4.1.0
./configure --prefix=/home/jacksund/vasp/02_mpfr/install --with-gmp=/home/jacksund/vasp/01_gmp/install
make -j 2
make install
make check
```

3. Install `mpc` 
``` bash
cd ~/vasp/03_mpc
tar xvzf *.tar.gz
cd mpc-1.2.1
./configure --prefix=/home/jacksund/vasp/03_mpc/install --with-gmp=/home/jacksund/vasp/01_gmp/install --with-mpfr=/home/jacksund/vasp/02_mpfr/install
make -j 2
make install
make check
```
 
4. Install `gcc`
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

5. Install `openmpi`
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

6. Install `fftw`
``` bash
cd ~/vasp/06_fftw
tar xvzf *.tar.gz
cd fftw-3.3.10
mkdir build
cd build
../configure --prefix=/home/jacksund/vasp/06_fftw/install
make -j 2
make install

nano ~/.bashrc
# ADD TO BOTTOM OF FILE
#
# export PATH=/home/jacksund/vasp/06_fftw/install/bin:$PATH

source ~/.bashrc
```

7. Install `lapack` (blas, cblas, lapacke, lapack)
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

8. Install `scalapack`
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

9. Install `vasp`
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

You can now use commands like `mpirun -n 4 vasp_std`!!! If you try this immediately, you'll see the "error" (VASP fails because no input files are present)..
``` bash
Error reading item 'VCAIMAGES' from file INCAR.
Error reading item 'VCAIMAGES' from file INCAR.
Error reading item 'VCAIMAGES' from file INCAR.
Error reading item 'VCAIMAGES' from file INCAR.
```