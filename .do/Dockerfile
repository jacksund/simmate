# This file sets up the environment for DigitalOcean to use on it's app platform.
# It is therefore only relevent if you are serving a Simmate website in production.
# We need this because we'd like to install all packages using Anaconda and 
# we'd also like to have Blender installed as well.
#
# This file was modified from DigitalOcean's examples located at...
#   https://github.com/digitalocean/sample-dockerfile
#   https://github.com/digitalocean/sample-python


# TO RUN THIS FILE: (be sure to update version)
# cd ~/Documents/github/simmate/
# docker login -u jacksund
# docker build -t jacksund/simmate:v0.9.0 -f .do/Dockerfile .
# docker push jacksund/simmate:v0.9.0

# Consider switching to latest instead of fixed version
#   https://hub.docker.com/_/ubuntu
FROM ubuntu:22.04

WORKDIR /root/

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
# Blender is automatically added to path

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
ENV CMD_PREFIX="conda run -n simmate_dev"

# This line copies the github repo's contents into our image
COPY . simmate_source
RUN $CMD_PREFIX pip install ./simmate_source && \
    $CMD_PREFIX pip install gunicorn psycopg2

# This is our "run command" that starts the Django server 
# CMD $CMD_PREFIX gunicorn --worker-tmp-dir /dev/shm simmate.website.core.wsgi
# --worker-tmp-dir is becuase of a DigitalOcean bug:
# https://docs.digitalocean.com/products/app-platform/reference/dockerfile/

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
#
#
# # This is the most widely used Blender image
# #   https://github.com/nytimes/rd-blender-docker/
# FROM nytimes/blender:latest as blender_build
# WORKDIR /root/blender
#
# # copy command is from https://stackoverflow.com/questions/55185389/
# COPY --from=miniconda_build /opt/conda/. /opt/conda/
# ENV PATH /opt/conda/bin:$PATH
#
# # TODO: separate stage for all the simmate steps that copy over
# # the basics from the blender/conda stages
# COPY tutorials/Guides_for_contributors/environment.yaml .
# RUN conda env update -f environment.yaml
# ENV CMD_PREFIX="conda run -n simmate_dev"
#
# This line copies the github repo's contents into our image
# COPY . simmate_source
# RUN $CMD_PREFIX pip install ./simmate_source
