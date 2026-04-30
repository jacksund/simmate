
FROM ubuntu:22.04
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

# Only dependencies required to install 'uv' are needed here.
RUN apt-get update && \
    apt-get install -y \
        curl \
        ca-certificates && \
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
    django-admin collectstatic --noinput

# =============================================================================
# Server
# =============================================================================

EXPOSE 8000

# Starts the Django app via Gunicorn on port 8000.
# '--worker-tmp-dir /dev/shm' is required due to a DigitalOcean App Platform bug:
# https://docs.digitalocean.com/products/app-platform/reference/dockerfile/
CMD ["gunicorn", \
     "--worker-tmp-dir", "/dev/shm", \
     "--bind", "0.0.0.0:8000", \
     "--access-logfile", "gunicorn_logging.out", \
     "simmate.website.server.wsgi"]
