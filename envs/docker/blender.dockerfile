
FROM ubuntu:22.04
WORKDIR /root/

# =============================================================================
# OS Dependencies
# =============================================================================

# Many dependencies are required for Blender. Full list available at:
# https://wiki.blender.org/wiki/Building_Blender/Linux/Ubuntu
RUN apt-get update && \
    apt-get install -y \
        wget \
        xz-utils \
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
