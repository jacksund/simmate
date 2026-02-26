
FROM ubuntu:22.04
WORKDIR /root/

# Setup up env variables. We do this before installing
# simmate + deps to keep the layer sizes down.
ENV PATH=/root/.venv/bin:/root/.local/bin:$PATH
ENV VIRTUAL_ENV=/root/.venv
ENV DJANGO_SETTINGS_MODULE="simmate.configuration.django.settings"
ENV DEBUG=False

# Install OS dependencies
# Many of these are for blender, where we got the full list from:
#   https://wiki.blender.org/wiki/Building_Blender/Linux/Ubuntu
RUN apt-get update && \
    apt-get install -y \
         wget \
         curl \
         xz-utils \
         build-essential \
         git subversion \
         cmake \
         libx11-dev \
         libxxf86vm-dev \
         libxcursor-dev \
         libxi-dev \
         libxrandr-dev \
         libxinerama-dev \
         libegl-dev && \
    apt-get clean

# Download and install Blender
RUN wget https://download.blender.org/release/Blender3.1/blender-3.1.0-linux-x64.tar.xz -O blender.tar.xz && \
    tar -xvf blender.tar.xz --strip-components=1 -C /bin && \
    rm blender.tar.xz
# Blender is automatically added to path

# Download and install uv
RUN curl -Ls https://astral.sh/uv/install.sh | sh
# Note: ~/.local/bin added to PATH at start of file

# Install Python and create a virtual environment using uv
RUN uv python install 3.11 && \
    uv venv /root/.venv --python 3.11
# Note: .venv added to PATH and VIRTUAL_ENV set at start of file

# Install Simmate's Python dependencies
COPY pyproject.toml .
RUN uv sync

# This line copies the github repo's contents into our image
COPY . simmate_source
RUN uv pip install -e ./simmate_source && \
    django-admin collectstatic

# -----------------------------------------------------------------------------

# This is our "run command" that starts the Django server and makes it available
# through the 8000 port (which is the same as the Django test server)
EXPOSE 8000
CMD gunicorn \
    --worker-tmp-dir /dev/shm \
    --bind 0.0.0.0:8000 \
    --access-logfile gunicorn_logging.out \
    simmate.website.core.wsgi
# The 'worker-tmp-dir' is becuase of a DigitalOcean bug:
# https://docs.digitalocean.com/products/app-platform/reference/dockerfile/

# -----------------------------------------------------------------------------
