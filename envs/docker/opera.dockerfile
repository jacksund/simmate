# -----------------------------------------------------------------------------

# This build script is based on the OPERA's official docs:
#   https://github.com/kmansouri/OPERA

# -----------------------------------------------------------------------------

# To build this image:
#   docker build -t jacksund/opera:v0.0.0 -f envs/docker/opera.dockerfile .

# -----------------------------------------------------------------------------

FROM ubuntu:18.04

# Install OS dependencies
RUN apt-get update && \
    apt-get install -y \
        wget \
        unzip \
        openjdk-8-jre && \
    apt-get clean

# Download & unpack OPERA source code + build files
RUN wget https://archives.simmate.org/OPERA2.9_CL_mcr.tar.gz -O opera.tar.gz --no-check-certificate && \
    tar -xzf opera.tar.gz && \
    rm opera.tar.gz

# Install OPERA
RUN ./OPERA2_CL_mcr/OPERA2.9_mcr_Installer.install -mode silent -agreeToLicense yes && \
    rm -rf OPERA2_CL_mcr

# Set ENV vars as directed by docs
ENV MATLAB_DIR=/usr/local/MATLAB/MATLAB_Runtime/v912
ENV XAPPLRESDIR=$MATLAB_DIR/X11/app-defaults
ENV LD_LIBRARY_PATH=$MATLAB_DIR/runtime/glnxa64:$MATLAB_DIR/bin/glnxa64:$MATLAB_DIR/sys/os/glnxa64:$MATLAB_DIR/sys/opengl/lib/glnxa64

# BUG: OPERA only works when located here
RUN mv /usr/OPERA /usr/local/bin

# BUG: setting path doesn't work because it matches the folder name in bin.....
# Therefore the full path to the exe is required.
# ENV PATH="${PATH}:/usr/local/OPERA/application/"

# build a working directory to run calculations
RUN mkdir opera_calc/
WORKDIR opera_calc/


# We do not provide a CMD or ENTRYPOINT in case the user 
# wants to open the container interactively.
# The command should look something like:
#   /usr/local/bin/OPERA/application/OPERA -s inputs.smi -o output.csv
# The default CMD is for an interactive pod:
CMD ["tail", "-f", "/dev/null"]

# -----------------------------------------------------------------------------
