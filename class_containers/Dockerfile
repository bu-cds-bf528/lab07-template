# micromamba is a stripped down version of mamba
# mamba is an improved implementation of conda
FROM mambaorg/micromamba:latest

# Copy the yml file into the container and set it's permissions to be
# owned by the MAMBA_USER and not root
COPY --chown=$MAMBA_USER:$MAMBA_USER fastqc_env.yml /fastqc_env.yml

# Installs the environment, cleans up caches and other unnecessary files
RUN micromamba install -y -n base -f /fastqc_env.yml && micromamba clean --all --yes

# ROOT permissions are required for certain operations
USER root

# required for nextflow trace - apt-get is a debian package manager and we're
# installing procps for nextflow

# We can safely remove /var/lib/apt/lists/* after the install in this image
RUN apt-get update && apt-get install -y procps && rm -rf /var/lib/apt/lists/*

# Switch back to the MAMBA_USER
USER $MAMBA_USER

# This is what enables the micromamba commands to be run from the container
# without specifying the full path to where the tools are installed
ENV PATH "$MAMBA_ROOT_PREFIX/bin:$PATH"