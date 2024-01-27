# This build script is based on the Bader's official docs:
#   http://theory.cm.utexas.edu/henkelman/code/bader/

# -----------------------------------------------------------------------------

# To build this image: (be sure to update version)
#   cd ~/Documents/github/simmate/
#   docker login -u jacksund
#   docker build -t jacksund/bader:v0.0.0 -f envs/docker/bader.dockerfile .
#   docker push jacksund/bader:v0.0.0

# -----------------------------------------------------------------------------

# TODO: consider making another image that includes extra bader scripts: 

# 1. Download the scripts from [VTST-tools](http://theory.cm.utexas.edu/vtsttools/scripts.html)
# 2. Unzip the folder (`vtstscripts-1033`) and move it to the directory where your bader executable is located.
# 3. Run `nano ~/.bashrc` to modify your bash and add this line at the end:
# ``` bash
# # Make sure to update the 'myname' part!
# export PATH=/home/myname/bader/vtstscripts-1033:$PATH
# ```

# -----------------------------------------------------------------------------

FROM ubuntu:18.04

# Install OS dependencies
RUN apt-get update && \
    apt-get install -y \
        wget \
        gfortran && \
    apt-get clean

# Download & unpack Bader source code + build files
# NOTE: we are pulling the downloads directly from Simmate's CDN, but these 
# are exactly the same as the files downloaded from the Bader website.
RUN wget https://archives.simmate.org/bader_v1.05_Release.tar.gz -O bader.tar.xz && \
    tar -zxvf bader.tar.xz && \
    mkdir bader_bin && \
    cp bader bader_bin/bader && \
    rm bader.tar.xz bader

# Bader is a plain executable. No installation is needed. We just add it to the path.
ENV PATH="${PATH}:/bader_bin/"

# build a working directory to run calculations
RUN mkdir bader_calc/
WORKDIR bader_calc/

# Command to call Bader.
# This entrypoint must be overwritten when the user's actual command to run 
# (assumes input files are provided by user via volumes)
ENTRYPOINT bader CHGCAR
