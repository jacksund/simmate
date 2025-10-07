# -----------------------------------------------------------------------------

# This build script is based on the Psi4's official docs:
#   https://psicode.org/installs/v191/

# Note that there are a bunch of ways to install -- and there's even
# an official docker image:
#   https://hub.docker.com/r/psi4/psi4 

# -----------------------------------------------------------------------------

# To build this image:
#   docker build -t jacksund/psi4:v0.0.0 -f envs/docker/psi4.dockerfile .

# -----------------------------------------------------------------------------

FROM ubuntu:22.04
WORKDIR /root/

ENV PATH=/root/miniforge/bin:$PATH
ENV CMD_PREFIX="conda run -n psi4_env"

# Install OS dependencies
RUN apt-get update && \
    apt-get install -y \
        wget \
        gfortran && \
    apt-get clean

# Download and install Miniforge (conda)
RUN wget https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh -O ~/miniforge.sh && \
    bash miniforge.sh -b -p miniforge && \
    rm miniforge.sh

# Install Psi4 via conda-forge
RUN conda create -y -c conda-forge -n psi4_env python=3.11 psi4 && \
    conda clean -afy

# build a working directory to run calculations
RUN mkdir psi4_calc/
WORKDIR psi4_calc/

# We do not provide a CMD or ENTRYPOINT in case the user 
# wants to open the container interactively.
# The command should look something like:
#   psi4 input.dat output.dat

# -----------------------------------------------------------------------------
