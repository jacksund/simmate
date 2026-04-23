# This build script installs VASP 5.4.4 on Ubuntu 22.04.
# It follows the official VASP installation instructions for personal computers.
# See: https://www.vasp.at/wiki/index.php/Personal_computer_installation

# -----------------------------------------------------------------------------

# NOTE: The VASP source files are private assets and must be obtained 
# from https://archives.simmate.org/vasp_5.4.4.zip
# Access to this file is restricted to licensed VASP users.

# -----------------------------------------------------------------------------

# To build this image:
#   docker build -t simmate-vasp -f envs/docker/vasp.dockerfile .

# -----------------------------------------------------------------------------

FROM ubuntu:22.04

# Avoid interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install base OS dependencies and required libraries for VASP
# Note: libfftw3-dev, libopenblas-dev, libopenmpi-dev, libscalapack-openmpi-dev, 
# and libhdf5-openmpi-dev are all required for the standard build.
RUN apt-get update && \
    apt-get install -y \
        rsync \
        make \
        build-essential \
        g++ \
        gfortran \
        wget \
        unzip \
        curl \
        libopenblas-dev \
        libopenmpi-dev \
        libscalapack-openmpi-dev \
        libfftw3-dev \
        libhdf5-openmpi-dev && \
    apt-get clean

# Set the working directory for the build process
WORKDIR /opt/vasp

# Download and unpack VASP source bundle
# Note: This is a private asset.
RUN wget https://archives.simmate.org/vasp_5.4.4.zip -O vasp_bundle.zip && \
    unzip vasp_bundle.zip && \
    rm vasp_bundle.zip

# The zip is expected to contain the vasp source files in a folder like vasp.5.4.4
# We move them to the root of /opt/vasp for simplicity if they are in a subfolder.
# If they are already in the root, this command will just fail silently.
RUN mv vasp.5.4.4/* . || true

# Prepare the makefile.include from the gnu_omp template
# Note: For VASP 5.4.4, the template might be slightly different or named linux_gfortran
# but we follow the wiki's recommendation for modern systems.
RUN cp arch/makefile.include.gnu_omp makefile.include || \
    cp arch/makefile.include.linux_gfortran makefile.include

# Customize makefile.include based on the VASP Wiki instructions:
# 1. BLAS & LAPACK: Use system openblas
# 2. ScaLAPACK: Use system openmpi scalapack
# 3. FFTW: Use system fftw
# 4. HDF5: Add support (Recommended)
RUN sed -i 's/^OPENBLAS_ROOT/#&/' makefile.include && \
    sed -i 's/^BLASPACK = .*/BLASPACK = -lopenblas/' makefile.include && \
    sed -i 's/^SCALAPACK_ROOT/#&/' makefile.include && \
    sed -i 's/^SCALAPACK = .*/SCALAPACK = -lscalapack-openmpi/' makefile.include && \
    sed -i 's/^FFTW_ROOT/#&/' makefile.include && \
    sed -i 's/^LLIBS += -L$(FFTW_ROOT).*/LLIBS += -lfftw3 -lfftw3_omp/' makefile.include && \
    sed -i 's/^INCS += -I$(FFTW_ROOT).*/INCS += -I\/usr\/include/' makefile.include && \
    # HDF5 Support: append to CPP_OPTIONS and add LLIBS/INCS
    sed -i 's/^CPP_OPTIONS =/CPP_OPTIONS = -DVASP_HDF5 /' makefile.include && \
    echo "LLIBS += -L/usr/lib/x86_64-linux-gnu/hdf5/openmpi/ -lhdf5_fortran" >> makefile.include && \
    echo "INCS += -I/usr/include/hdf5/openmpi/" >> makefile.include

# Compile VASP
# We build the standard (std) version. 
# Others like gam, ncl can be added with 'make std gam ncl'
RUN make DEPS=1 -j$(nproc) std

# Add VASP binaries to the path
ENV PATH="/opt/vasp/bin/:${PATH}"

# Set OMP_NUM_THREADS=1 for pure MPI parallelization as recommended
ENV OMP_NUM_THREADS=1

# Create a working directory to run calculations
RUN mkdir /vasp_calc
WORKDIR /vasp_calc

# Typical usage: mpirun -n 4 vasp_std
