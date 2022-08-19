# This file sets up the environment for DigitalOcean to use on it's app platform.
# It is therefore only relevent if you are serving a Simmate website in production.
# We need this because we'd like to install all packages using Anaconda and 
# we'd also like to have Blender installed using the snapcraft store.
#
# This file was modified from DigitalOcean's examples located at...
#   https://github.com/digitalocean/sample-dockerfile
#   https://github.com/digitalocean/sample-python

# Consider switching to latest instead of fixed version
#   https://hub.docker.com/_/ubuntu
FROM ubuntu:22.04

WORKDIR /root/

# This is our "build command", which installs Miniconda, Blender, Simmate, and all of Simmates dependencies

# Install OS dependencies
# Many of these are for blender, where we got the full list from:
#   https://wiki.blender.org/wiki/Building_Blender/Linux/Ubuntu
RUN apt-get update && \
    apt-get install -y \
        wget \
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
# Blender is automaticall added to path

# Download and install Miniconda
RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh && \
    bash miniconda.sh -b -p miniconda && \
    rm miniconda.sh
# Add conda to the path
ENV PATH=/root/miniconda/bin:$PATH

# Install Simmate's Python dependencies 
COPY tutorials/Guides_for_contributors/environment.yaml .
RUN conda env update -f environment.yaml
# Make sure we are always using the simmate_dev env with
# any commands below.
# SHELL ["/bin/sh", "-c", "conda", "run", "-n", "simmate_dev"]
# BUG: This line above doesn't work so I have to write it out
# for every command below
ENV CMD_PREFIX="conda run -n simmate_dev"

# This line copies the github repo's contents into our image
COPY . simmate_source
RUN $CMD_PREFIX pip install ./simmate_source

# This is our "run command" that starts the Django server 
# CMD ["HELLO"]

# DEV NOTES:
# I could alternatively use third-party builds for miniconda and blender.
# This would involve a multi-stage build, where I have a semi-working
# version below. These are kept as notes for possible future use. 
#
#
# # This is the official Anaconda image
# #   https://docs.anaconda.com/anaconda/user-guide/tasks/docker/
# #   https://hub.docker.com/u/continuumio
# FROM continuumio/miniconda3 as miniconda_build
# # TODO: organize first two stages into folders using WORKDIR
# # or alternatively alter the COPY command to localize them
# # WORKDIR /blender
#
# # This is the most widely used Blender image
# #   https://github.com/nytimes/rd-blender-docker/
# FROM nytimes/blender:latest as blender_build
# ENV PATH /opt/conda/bin:$PATH
#
# # copy command is from https://stackoverflow.com/questions/55185389/
# COPY --from=miniconda_build /opt/conda/. /opt/conda/
#
# # TODO: separate stage for all the simmate steps that copy over
# # the basics from the blender/conda stages
# COPY tutorials/Guides_for_contributors/environment.yaml .
# RUN conda env update -f environment.yaml
# # BUG: I can't figure out how to activate the conda env, and it looks like
# # there are a ton of people asking for help online too. To get around this,
# # it seems like I just need to use... "conda run -n simmate_dev <my-command>"
# # For example:
# # conda run -n simmate_dev simmate database reset --confirm-delete --use-prebuilt false
#
# # This line copies the github repo's contents into our image
# COPY . .
# RUN conda run -n simmate_dev pip install .
