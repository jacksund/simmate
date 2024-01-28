# This build script is largely based on the QE repo's official .gitlab-ci-main.yml:
#   https://github.com/QEF/q-e/blob/bd7c3d45af70bd7c2015cc33dbcf20906dc37dae/.gitlab-ci-main.yml#L3-L15

# -----------------------------------------------------------------------------

# To run a container + a single QE calculation, the user must provide...
#   (1) an pwscf.in file (the pw.x input)
#   (2) all required psuedopotentials (*.usp files, typically in a single directory)
#   (3) a command via "sh -c"
# The input files are normally given as volumes. This image will run then calculation.

# Example:
#   docker run --volume path/to/my/inputs:/qe_calc --volume path/to/potentials:/potentials jacksund/quantum-espresso:v0.0.0 sh -c "pw.x < pwscf.in > pw-scf.out"

# -----------------------------------------------------------------------------

# To build this image: (be sure to update version)
#   cd ~/Documents/github/simmate/
#   docker login -u jacksund
#   docker build -t jacksund/quantum_espresso:v0.0.0 -f envs/docker/quantum_espresso.dockerfile .
#   docker push jacksund/quantum_espresso:v0.0.0

# Consider trying cmake instead of make for builds outside of docker:
#   https://gitlab.com/QEF/q-e/-/wikis/Developers/CMake-build-system

# -----------------------------------------------------------------------------

FROM ubuntu:18.04

# Install OS dependencies
RUN apt-get update && \
    apt-get install -y \
        m4 \
        make \
        wget \
        curl \
        git \
        gfortran \
        gcc \
        libopenblas-dev \
        libfftw3-dev \
        libopenmpi-dev && \
    apt-get clean

# Download & unpack Quantum Espresso source code + build files
# NOTE: we are pulling the downloads directly from Simmate's CDN, but these 
# are exactly the same as the files downloaded from the QE website.
RUN wget https://archives.simmate.org/qe-7.2-ReleasePack.tar.gz -O qe-7.2.tar.xz  && \
    tar -zxvf qe-7.2.tar.xz && \
    rm qe-7.2.tar.xz

# Open of build files and install Quantum Espresso's pw.x
# We remove all install/build files at the end too
RUN cd qe-7.2 && \
    ./configure && \
    make pw && \
    make install && \
    cd .. && \
    rm -r qe-7.2

# build a working directory to run calculations
RUN mkdir qe_calc/
WORKDIR qe_calc/

# We do not provide a CMD or ENTRYPOINT in case the user 
# wants to open the container interactively.
# The command should look something like:
#   pw.x < pwscf.in > pwscf.out
