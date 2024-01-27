# This build script is based on the Bader's official docs:
#   http://theory.cm.utexas.edu/henkelman/code/bader/

# -----------------------------------------------------------------------------

# To build this image: (be sure to update version)
#   cd ~/Documents/github/simmate/
#   docker login -u jacksund
#   docker build -t jacksund/bader:v0.0.0 -f envs/docker/bader.dockerfile .
#   docker push jacksund/bader:v0.0.0

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
RUN wget https://archives.simmate.org/bader_v1.05_Release.tar.gz -O bader.tar.xz  --no-check-certificate && \
    tar -zxvf bader.tar.xz && \
    rm bader.tar.xz

# Bader is a plain executable. No installation is needed. We just add it to the path.
# ENV PATH="${PATH}:/path/to/baderfolder/"

# build a working directory to run calculations
RUN mkdir bader_calc/
# WORKDIR bader_calc/

# Command to call Bader.
# This entrypoint must be overwritten when the user's actual command to run 
# (assumes input files are provided by user via volumes)
# ENTRYPOINT bader
