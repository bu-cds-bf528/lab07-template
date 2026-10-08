---
title: "Lab 06 — Docker and Containers"
---

## Goals

- Pull and inspect existing Docker images from Docker Hub
- Write a `Dockerfile` from scratch and build a working image
- Run containers interactively and non-interactively
- Use a bind mount to retrieve output files from a container
- Push an image to GitHub Container Registry (GHCR)
- Understand how Docker images become Singularity containers in Nextflow pipelines

## Background

Containers solve the "works on my machine" problem by bundling a tool and all its dependencies into a single portable image. Any machine running Docker (or Singularity) can reproduce the exact same environment — the same tool version, the same library versions, the same behavior — regardless of what is installed on the host system.

This is why Nextflow pipelines specify `container 'ghcr.io/bf528/...'`: every job runs inside a container pulled from the registry rather than relying on software being installed on the cluster node.

This lab runs in **GitHub Codespaces** rather than the SCC because the SCC does not grant users access to the Docker daemon. Codespaces provides a full Ubuntu environment with Docker pre-installed.

## Key Concepts

### Images vs. Containers

An **image** is a read-only template: a packaged filesystem plus metadata (like the default `CMD`) that is built once from a Dockerfile or pulled from a registry. A **container** is a running (or stopped) instance created from an image, with its own writable layer on top. The relationship is like a class and an object, or a recipe and a meal: one image can be used to start many independent containers, and changes made inside a container never alter the image it came from.

| | Image | Container |
|---|---|---|
| What it is | Read-only template | Running or stopped instance of an image |
| Created with | `docker build`, `docker pull` | `docker run` |
| Listed with | `docker images` | `docker ps -a` |
| Removed with | `docker rmi` | `docker rm` |
| Shared via | Registries (Docker Hub, GHCR) | Not shared; local to your machine |

### Images

**Dockerfile keywords**

| Keyword | Purpose |
|---|---|
| `FROM` | Set the base image to build on top of |
| `RUN` | Execute a shell command during the build (installs software, cleans up, etc.) |
| `COPY` | Copy a file from the host into the image |
| `WORKDIR` | Set the working directory for subsequent instructions and the container's default shell |
| `CMD` | Default command to run when a container starts |

**Build cache** — Docker caches each layer. If a layer's instruction and its inputs haven't changed since the last build, Docker reuses the cached result and skips re-running it. Placing instructions that change rarely (e.g., `COPY requirements.txt` + `RUN pip install`) before instructions that change often (e.g., `COPY script.py`) keeps builds fast.

**Image tags** — Tags are version labels attached to an image name: `python_script:latest`, `python_script:v1.0`. The `latest` tag is applied by default if none is specified. Tagging an image with a registry path (`ghcr.io/<user>/<image>:tag`) is required before pushing.

**GHCR and Singularity** — GitHub Container Registry hosts Docker images associated with GitHub accounts. When you run Nextflow with `-profile singularity`, Nextflow pulls Docker images from GHCR and Singularity converts them into `.sif` files it can run in the cluster's unprivileged environment.

### Containers

**Running modes** — `docker run <image>` creates a container and runs the image's `CMD`. The container stops as soon as that command finishes. `docker run -it <image> bash` overrides the `CMD` and attaches your terminal to a shell inside the container, which is useful for exploring and debugging. Adding `--rm` deletes the container automatically when it stops.

**Container lifecycle** — A stopped container still exists (and still takes up disk space) until you remove it with `docker rm`. Container names must be unique, so you cannot reuse a `--name` until the old container is removed. An image cannot be removed while any container, even a stopped one, was created from it.

**Bind mounts** — Containers have an isolated filesystem. Files created inside a container are lost when the container is removed unless you mount a host directory into the container with `-v $(pwd):/app`. Writes to `/app` inside the container are written to your current directory on the host. The mount also hides whatever was at `/app` in the image.

## Approaches to Building Images

Every Dockerfile has to answer the same question: how does the tool get installed into the image? Most bioinformatics images use one of three approaches. Each one trades off build time, image size, and how much control you have over the result.

### Compiling from source

You download the tool's source code and compile it inside the image. This gives you the most control: you choose the exact version, compiler flags, and optional features. It is often the only option for tools that are new, patched, or not packaged anywhere else.

The downside is that you have to install the full build toolchain (compilers, `make`, development headers for every library the tool links against). That makes images large and builds slow, and you have to work out the dependencies yourself, usually from the tool's `INSTALL` file or from trial and error.

```dockerfile
FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential wget ca-certificates \
        zlib1g-dev libbz2-dev liblzma-dev libncurses-dev libcurl4-openssl-dev \
    && rm -rf /var/lib/apt/lists/*

RUN wget https://github.com/samtools/samtools/releases/download/1.21/samtools-1.21.tar.bz2 \
    && tar -xjf samtools-1.21.tar.bz2 \
    && cd samtools-1.21 && ./configure && make && make install \
    && cd .. && rm -rf samtools-1.21*
```

**Multi-stage builds** help with the size problem. You compile the tool in a first "builder" stage that has all the compilers, then `COPY --from=builder` only the finished program (and the runtime libraries it needs) into a clean, slim second stage. The compilers never end up in the final image.

### Downloading pre-compiled binaries

Many tools publish ready-to-run executables on their releases page, such as a GitHub release, a `.zip`, or a single static binary. Your Dockerfile downloads the file, unpacks it, and puts it on the `PATH`. Nothing is compiled, so builds are fast and images stay small.

You do have to make sure the binary matches the image's CPU architecture (e.g. `x86_64` vs `arm64`) and that any runtime it depends on is installed. For example, FastQC needs Java:

```dockerfile
FROM eclipse-temurin:17-jre

RUN apt-get update && apt-get install -y --no-install-recommends wget unzip \
    && rm -rf /var/lib/apt/lists/*

RUN wget https://www.bioinformatics.babraham.ac.uk/projects/fastqc/fastqc_v0.12.1.zip \
    && unzip fastqc_v0.12.1.zip -d /opt \
    && rm fastqc_v0.12.1.zip \
    && chmod +x /opt/FastQC/fastqc

ENV PATH="/opt/FastQC:$PATH"
```

### Installing with conda / mamba

Start from an image that already has a package manager (`continuumio/miniconda3`, `mambaorg/micromamba`). Write the tools and versions you need in an environment YML file, then let conda work out and install all the dependencies. Bioconda already packages thousands of bioinformatics tools, so this is usually the quickest way to get a working image. A YML file with pinned versions also documents exactly what is in the image.

Conda environments can be large, though, and solving complex environments can be slow. Images from this approach are often bigger than ones built from source or binaries. Use `micromamba` instead of full conda, and clean caches in the same `RUN` instruction (`micromamba clean --all --yes`), to keep the size down.

This is the approach used for the BF528 course containers (see `class_containers/`) and the one you'll use in the advanced section of the lab.

### Choosing an approach

| Approach | Build speed | Image size | Control | Best when... |
|---|---|---|---|---|
| Compile from source | Slow | Large (unless multi-stage) | Full | No package or binary exists, or you need a specific build |
| Pre-compiled binary | Fast | Small | Limited to what's released | The tool ships official binaries for your architecture |
| Conda / mamba | Moderate | Moderate–large | Pinned versions via YML | The tool is on bioconda / conda-forge (most bioinformatics tools) |

Before writing a Dockerfile at all, check whether someone already maintains an image: the tool's own docs, [BioContainers](https://biocontainers.pro/) (which automatically builds an image for every bioconda package), or `ghcr.io/bf528/` for this course. Whichever approach you use, always **pin versions** (`samtools-1.21`, `fastqc=0.12.1`, not `latest`), so rebuilding the image later gives you the same software.

## Commands Reference

### Images

```bash
# Pull an image from a registry
docker pull <image>:<tag>

# Build an image from the Dockerfile in the current directory
docker build -t <image>:<tag> .

# List images
docker images

# Remove an image
docker rmi <image>:<tag>

# Tag an image for a registry
docker tag <image>:latest ghcr.io/<username>/<image>:latest

# Authenticate to GHCR (Codespaces provides GITHUB_TOKEN automatically)
echo $GITHUB_TOKEN | docker login ghcr.io -u $GITHUB_USER --password-stdin

# Push to GHCR
docker push ghcr.io/<username>/<image>:latest
```

### Containers

```bash
# Run a container (non-interactive, executes CMD)
docker run --name <name> <image>

# Run a container interactively (removed automatically on exit)
docker run -it --rm <image> bash

# Run with a bind mount
docker run -v $(pwd):/app --name <name> <image>

# List all containers, including stopped ones
docker ps -a

# Remove a container / all stopped containers
docker rm <name>
docker container prune
```
