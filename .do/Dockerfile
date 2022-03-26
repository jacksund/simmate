# This file sets up the environment for DigitalOcean to use on it's app platform.
# It is therefore only relevent if you are serving a Simmate website in production.
# We need this because we'd like to install all packages using Anaconda and 
# we'd also like to have Blender installed using the snapcraft store.
#
# This file was modified from DigitalOcean's examples located at...
#   https://github.com/digitalocean/sample-dockerfile
#   https://github.com/digitalocean/sample-python
#
# DEV NOTE:
# I couldn't figure out multi-staged Docker builds that combine images, so I
# can't take advantage of the Blender and Anaconda images below...
#   https://docs.docker.com/develop/develop-images/multistage-build/
#
# This is the most widely used Blender image
#   https://github.com/nytimes/rd-blender-docker/
# FROM nytimes/blender:latest
#
# This is the official Anaconda image
#   https://docs.anaconda.com/anaconda/user-guide/tasks/docker/
#   https://hub.docker.com/u/continuumio
# FROM continuumio/miniconda3 as builder


# Consider switching to latest instead of fixed version
#   https://hub.docker.com/_/ubuntu
FROM ubuntu:22.04

WORKDIR /root/

# This line copies the github repo's contents into our image
COPY . .

# This is our "build command", which installs Miniconda, Blender, Simmate, and all of Simmates dependencies

# Install OS dependencies
RUN apt-get update && \
    apt-get install -y wget blender && \
    apt-get clean

# Download and install Miniconda
RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh && \
    bash ~/miniconda.sh -b -p $HOME/miniconda && \
    $HOME/miniconda/bin/conda --version
# $HOME/miniconda/bin/conda env update -f tutorials/Guides_for_contributors/environment.yaml --> runs out of memory

# Add conda to the path (not sure which method is correct here...)
ENV PATH=$HOME/miniconda/bin:$PATH
# Make RUN commands use the new environment:
#SHELL ["conda", "run", "-n", "simmate_dev", "/bin/bash", "-c"]
# RUN conda --version  <-- fails

# Download and install Blender
# The method above (apt-get) is typically out of date, but it works... Meanwhile the more robust
# way (below) is throwing a bunch of errors. If I want to return to trying this
# method, I need to remove Blender from apt-get (above) and replace it with xz-utils
#RUN wget https://download.blender.org/release/Blender3.1/blender-3.1.0-linux-x64.tar.xz && \
#	tar -xvf blender-3.1.0-linux-x64.tar.xz --strip-components=1 -C /bin && \
#   rm blender-3.1.0-linux-x64.tar.xz && \
#   ./blender-3.1.0-linux-x64/blender --version

# This is our "run command" that starts the Django server 
CMD ["HELLO"]
