
FROM docker.io/library/ubuntu:22.04
WORKDIR /root/

# =============================================================================
# Environment Variables
# =============================================================================

ENV PATH=/root/simmate/.venv/bin:/root/.local/bin:$PATH \
    VIRTUAL_ENV=/root/simmate/.venv \
    UV_WORKING_DIR=/root/simmate \
    DJANGO_SETTINGS_MODULE="simmate.config.django.settings" \
    SIMMATE_CONFIG_DIR=/root/simmate-config \
    SIMMATE__WEBSITE__STATIC_FILE_HASHES="true" \
    DEBUG=False

# =============================================================================
# OS Dependencies
# =============================================================================

# Only dependencies required to install 'uv' and run 'rdkit' are needed here.
RUN apt-get update && \
    apt-get install -y \
        curl \
        ca-certificates \
        libxrender1 \
        libxext6 \
        libsm6 \
        libexpat1 \
        libfontconfig1 \
        libglib2.0-0 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

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
    simmate dev download-ketcher && \
    django-admin collectstatic --noinput

# =============================================================================
# Server
# =============================================================================

EXPOSE 8000

# Starts the Django app via Gunicorn on port 8000.
# '--worker-tmp-dir /dev/shm' is required due to a DigitalOcean App Platform bug:
# https://docs.digitalocean.com/products/app-platform/reference/dockerfile/
# '--threads 4' lets a request that is slow because it is *waiting* (i.e. I/O
# bound, such as a database query) run without freezing the site for everyone
# else. This does NOT help with CPU-bound requests: there is still only one
# worker process, and python runs one thread at a time while computing. We use
# threads rather than more '--workers' because htmx components are kept in the
# memory of a single process (see `simmate.website.htmx.components.base`),
# which all threads share.
CMD ["gunicorn", \
     "--worker-tmp-dir", "/dev/shm", \
     "--threads", "4", \
     "--bind", "0.0.0.0:8000", \
     "--access-logfile", "gunicorn_logging.out", \
     "simmate.website.server.wsgi"]
