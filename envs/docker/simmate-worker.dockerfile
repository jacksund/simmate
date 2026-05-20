FROM ubuntu:22.04

# Avoid interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /root/

# =============================================================================
# Environment Variables
# =============================================================================

ENV PATH=/root/simmate/.venv/bin:/root/.local/bin:$PATH \
    VIRTUAL_ENV=/root/simmate/.venv \
    UV_WORKING_DIR=/root/simmate \
    DJANGO_SETTINGS_MODULE="simmate.config.django.settings" \
    DEBUG=False

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
        wget \
        libxrender1 \
        libxext6 \
        libsm6 \
        libexpat1 \
        libfontconfig1 \
        libglib2.0-0 && \
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
# Python (via uv)
# =============================================================================

# Install uv — adds to ~/.local/bin, which is already on PATH
RUN curl -Ls https://astral.sh/uv/install.sh | sh

# =============================================================================
# Simmate
# =============================================================================

# Copy source and install Python dependencies
COPY . simmate
RUN uv sync && \
    uv pip install gunicorn && \
    django-admin collectstatic --noinput

# =============================================================================
# Worker Setup
# =============================================================================

# Sets up a directory for worker execution so we don't clutter /root
RUN mkdir /simmate_workers
WORKDIR /simmate_workers

CMD ["simmate", "compute", "start-worker"]
