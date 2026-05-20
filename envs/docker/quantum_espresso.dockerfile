# Dockerfile to compile and install Quantum Espresso (pw.x) on Ubuntu 22.04.

FROM ubuntu:22.04

# Avoid interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# =============================================================================
# OS Dependencies
# =============================================================================

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        gcc \
        gfortran \
        git \
        libfftw3-dev \
        libopenblas-dev \
        libopenmpi-dev \
        m4 \
        make \
        wget && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# =============================================================================
# Quantum Espresso (Compilation & Installation)
# =============================================================================

# Downloads are pulled from Simmate's CDN. All steps are in a single RUN
# statement to avoid persisting transient source/tar files in intermediate layers.
RUN wget https://archives.simmate.org/qe-7.2-ReleasePack.tar.gz -O qe-7.2.tar.gz && \
    tar -xzf qe-7.2.tar.gz && \
    rm qe-7.2.tar.gz && \
    cd qe-7.2 && \
    ./configure && \
    make pw && \
    make install && \
    cd .. && \
    rm -rf qe-7.2

# =============================================================================
# Execution Setup
# =============================================================================

RUN mkdir /qe_calc
WORKDIR /qe_calc
