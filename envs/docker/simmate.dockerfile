
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

# Many dependencies are required for Blender. Full list available at:
# https://wiki.blender.org/wiki/Building_Blender/Linux/Ubuntu
RUN apt-get update && \
    apt-get install -y \
        wget \
        curl \
        xz-utils \
        build-essential \
        git \
        subversion \
        cmake \
        libx11-dev \
        libxxf86vm-dev \
        libxcursor-dev \
        libxi-dev \
        libxrandr-dev \
        libxinerama-dev \
        libegl-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# =============================================================================
# Blender
# =============================================================================

RUN wget https://download.blender.org/release/Blender3.1/blender-3.1.0-linux-x64.tar.xz -O blender.tar.xz && \
    tar -xf blender.tar.xz --strip-components=1 -C /bin && \
    rm blender.tar.xz

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
     "simmate.website.core.wsgi"]
