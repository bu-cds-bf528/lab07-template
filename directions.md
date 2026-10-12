# Lab 06 - Docker

## Objectives

- Gain familiarity with common Docker commands: FROM, RUN, COPY, WORKDIR, CMD

- Understand Docker build cache

- Learn how to run docker containers non-interactively and interactively

- Follow general best practices to make containers reproducible, and lightweight

- Use a bind-mount to persist files generated in a container on the host

- Push an image to the GitHub Container Registry (GHCR)

## Accept the github classroom repository

Instead of cloning this repo to the SCC, we are instead going to use the github 
codespaces functionality, which allows you to open an integrated development
environment in the cloud using the repository as a template. By default, this
environment is created from an Ubuntu image and pre-installed with a selection 
of popular tools and utilities, including Docker. (We cannot use the SCC for
this lab because it does not give users access to the Docker daemon.)

After you accept the github classroom link, please go directly to the github
repository and click on the large green `code` button. Switch to the `codespaces`
tab and use the `Create codespace on main` button.

Once the codespace finishes loading, open a terminal (`Terminal` → `New Terminal`
if one is not already open).

## Basic Docker Commands

### Pulling an image

One of the huge advantages of Docker is the wide availability of ready-to-go and
verified containers. 

For now, run the following command in your terminal:

```
docker pull python
```

Because we did not specify a tag, Docker pulls the `latest` tag by default.

Use the `docker images` command to view the images you have available on your system.

```bash
# view all images available
docker images
```

What version of python is installed? Can you tell from the output of the `docker
images` command? 

To find out what version of python is installed, you can use the `docker run`
command to start a container from the image and then open a bash shell to
interact with the container.

```bash
# start and run a container built from the python image 
# and open a bash shell
docker run -it python bash
```

This will start a container from the python image and open a bash shell to
interact with the container. Your prompt will change to something like
`root@<container-id>:/#`, which tells you that you are now inside the container
rather than in your codespace. You can then use the `python --version` command
to see what version of python is installed.

```bash
python --version
```

What version of python is installed?

When you are done, you can exit the container by typing `exit` and pressing enter.

### Pulling a specific version of an image

Back on the docker hub python image page, click on the `Tags` tab. Find a tag
that is **not** `latest`, refers to an older version of python, and has `slim`
in the name (for example, `3.11-slim`).

Pull that tag by adding it after the image name with a colon:

```
docker pull python:<tag>
```

For example:

```
docker pull python:3.11-slim
```

Use the `docker images` command to view the images you have available on your system.

```
docker images
```

You should now see two `python` rows with different values in the TAG column.
Compare the SIZE column for the two images. Which is smaller, and what would 
explain the difference?

Try creating a container from the specific version of the python image you pulled,
similar to how we did it for the `latest` version above, and then run the `python
--version` command to see what version of python is installed.

```
docker run -it python:<tag> bash
```

What version of python is installed? Does it match the tag you chose?

When you are done, you can exit the container by typing `exit` and pressing enter.

## Creating a simple Docker image and container

Navigate to the simple/ directory:

```bash
cd simple
```

You'll notice that we have four files:

- `Dockerfile` - the instructions used to build the image
- `requirements.txt` - the python packages to install (biopython)
- `script.py` - a small script that calculates the GC content of a genome
- `genomeC.fna` - the genome fasta file the script reads

Briefly take a look at each file. Based on the lecture, you should be able to get
a rough sense for what the Dockerfile is doing: we are starting from a slim python
image, installing biopython, copying the script and the genome file into the image,
and then setting the script to run by default when a container starts.

Please use the following command to build a docker image from this Dockerfile.
The `-t` flag gives the image a name (`python_script`) and a tag (`latest`), and
the `.` at the end tells Docker to use the current directory as the build context
(the set of files `COPY` is allowed to use):

```bash
# build a container with the tag python_script:latest
docker build -t python_script:latest .
```

Upon completion, you should be able to see your docker image if you use the following command:

```
docker images
```

Take note of the difference between REPOSITORY and TAG as well as the size of the created
image.

### The build cache

Run the exact same build command a second time:

```
docker build -t python_script:latest .
```

It should finish almost instantly. Look at the build output: each step should be
marked `CACHED`. Docker saves the result of every instruction as a layer and reuses
it if neither the instruction nor the files it depends on have changed.

Now make a small change to `script.py`. For example, change the last line to:

```python
print(f'GC content: {gc_content}')
```

and rebuild:

```
docker build -t python_script:latest .
```

Which steps were `CACHED` this time and which were re-run? Notice that the
`pip install` step was still cached because `requirements.txt` did not change and
it comes *before* `COPY script.py` in the Dockerfile. If the order were reversed,
every edit to the script would force biopython to be re-installed. Ordering
instructions from least to most frequently changed is a key way to keep builds fast.

## Running a container from this image

We have only built the image, we still need to create a container or instance from this
image. 

Run the following command:

```
docker run --name test1 python_script
```

What do you expect the output to be? What is the output?

You should see the GC content of the genome printed as a decimal between 0 and 1,
and then you are returned to your terminal prompt. The container ran its `CMD`
(`python script.py`), and then exited because that command finished.

Try running the exact same command again. You will get an error that the name
`test1` is already in use. Container names must be unique, even for containers that
have stopped. Use `docker ps -a` to see the stopped `test1` container, then either
remove it with `docker rm test1` or choose a different name.

That was an example of running a docker container non-interactively. We can choose to run 
containers `interactively`, which you'll often use to debug or troubleshoot commands. The
following command will attach your terminal to the container's stdin/stdout so that you can 
interact with a bash shell or other program. Adding `bash` at the end overrides the
`CMD` in the Dockerfile, so the script does not run and you get a shell instead.
The `--rm` flag automatically deletes the container when you exit it.

```
docker run -it --rm python_script bash
```

Inside the container:

1. Run `pwd`. You should be in `/script`, the directory set by `WORKDIR`.
2. Run `ls`. You should see `requirements.txt`, `script.py`, and `genomeC.fna`,
   the files copied in by `COPY`. Notice that `Dockerfile` is **not** there. Why not?
3. Run `python` to open a python interpreter, then type `import Bio`. If no error
   appears, biopython was installed successfully by the `RUN` instruction. Type
   `exit()` to leave the interpreter.
4. Run `python script.py` to run the script by hand.

This is the environment that your container created and you should have access to
the same files you copied and the tools you installed in the Dockerfile. You may exit
the container using `exit`.

## A slightly more advanced version

Navigate to the advanced/ directory (from the root of the repository):

```
cd advanced
```

This directory contains:

- `Dockerfile` - partially written; you will fill in the missing lines
- `fastqc_env.yml` - empty; you will write it
- `example.fq.gz` - a small fastq file to run FastQC on

1. Using what we've just done, LLMs, or the internet, complete the files in this
directory to build an image with FastQC, create a container from it, and run fastqc
on the provided fastq.

    **fastqc_env.yml**

    - Create this YML file just as you've done for the other tools in this course
    - The environment `name` must be exactly `fastqc_env` (the Dockerfile adds
      `/opt/conda/envs/fastqc_env/bin` to the `PATH`, so any other name will not work)
    - Use the `conda-forge` and `bioconda` channels and install `fastqc`. You can
      look at `class_containers/fastqc_env.yml` for an example of the format.

    **Dockerfile** - fill in the three commented sections:

    - Set the working directory to `/app` using `WORKDIR`
    - Use `COPY` to copy both `fastqc_env.yml` and `example.fq.gz` into the image
    - Use `RUN` to create the conda environment. The command to create an
      environment from a file is `conda env create -f <yml_file>`
    - Do not change the lines marked "Don't change this"

Build the image using the following command (from inside `advanced/`):

```
docker build -t fastqc_container:latest .
```

Creating the conda environment can take a few minutes. If the build fails, read
the error message carefully. It will tell you which Dockerfile step failed.

You can check that FastQC was installed correctly before going further:

```
docker run --rm fastqc_container fastqc --version
```

2. Try running your container once:

```
docker run --name fastqc fastqc_container
```

Observe what happens. Does it run? Where is the output? Run `ls` in your
terminal. Do you see any new files in `advanced/`?

FastQC wrote `example_fastqc.html` and `example_fastqc.zip` to `/app` *inside the
container*, not onto your codespace. Recall that containers are isolated and by
default store any files non-persistently inside the container unless otherwise
specified. When a container is removed, any files inside will also be lost.
Typically speaking, we will want to persist files from a docker container to a more
permanent location. One way of accomplishing this is by using a bind-mount, which
will connect the host filesystem to the container filesystem and allow for various
read / write operations.

Add the `--volume` flag to your docker run command for a new container. Make sure
you run this from inside the `advanced/` directory:

```
docker run --volume $(pwd):/app --name fastqc2 fastqc_container
```

The `--volume` flag takes the form `<host_path>:<container_path>`. Here we bind
the present working directory on the host (`$(pwd)`, which is `advanced/`) to the
`/app` directory inside the container where FastQC is running and producing its
outputs.

Note that a bind-mount *replaces* whatever was at `/app` in the image with the
contents of your host directory. This works here because `example.fq.gz` also
exists in `advanced/` on the host. If you ran this command from a different
directory, FastQC would not be able to find the input file.

After you run this command, you should now see `example_fastqc.html` and
`example_fastqc.zip` appear in your `advanced/` directory. Prior to this, those
files only existed inside the container and would have been deleted along with it.
To view the report, right-click `example_fastqc.html` in the codespace file
explorer, choose `Download`, and open it in your browser.

## Managing your images and containers

Images and containers take up disk space, and codespaces have limited storage, so
it is good practice to clean up what you no longer need.

### Containers 

Use the `docker ps -a` command to view all the containers on your system, including
stopped ones (`docker ps` without `-a` only shows running containers).

```
docker ps -a
```

To remove a container, you can use the `docker rm` command.

```
docker rm <container_name / container ID>
```

To remove all stopped containers at once:

```
docker container prune
```

### Images

Use the `docker images` command to view all the images you have available on your system.

```
docker images
```

To remove an image, you can use the `docker rmi` command.

```
docker rmi <image_name:tag / image ID>
```

You must first remove any containers (including stopped ones) that were created
from an image before you can remove that image. Try removing the `python:latest`
image you pulled at the start of the lab, which you no longer need.

## BF528 Containers

Navigate to the class_containers/ directory. You do not need to build anything for
this part, but take a look at the `Dockerfile` and `fastqc_env.yml` contained within. 

These are how the containers we use for this class were built. Try to understand the
purpose of each line on your own. As you read, consider:

- How does the base image (`mambaorg/micromamba`) differ from the
  `continuumio/miniconda3` image you used in the advanced section?
- Why does the `RUN` line end with `micromamba clean --all --yes`, and why is
  `rm -rf /var/lib/apt/lists/*` part of the same `RUN` command as the install
  rather than a separate one?
- Why does the Dockerfile switch to `USER root` and then back to `USER $MAMBA_USER`?
- Why is there no `CMD`? (Hint: think about how Nextflow uses these containers.)

We'll go through it together and talk about the specific considerations that were
necessary. 

## Pushing your image to GitHub Container Registry

Every time you've used a container in your Nextflow pipelines — `container 'ghcr.io/bf528/<name>:latest'` — Nextflow pulled that image from the GitHub Container Registry (GHCR). GHCR works like Docker Hub but is tied to GitHub accounts and organizations. In this section you will tag the `python_script` image you already built and push it to your own GitHub account so that anyone (or any pipeline) could pull it.

In the commands below, replace `<your-github-username>` with your GitHub username
written in **all lowercase**. GHCR image names must be lowercase, so a username
like `JaneDoe` must be written as `janedoe`. You can print it with:

```
echo $GITHUB_USER | tr '[:upper:]' '[:lower:]'
```

### 1. Authenticate to GHCR

GitHub Codespaces automatically provides a `GITHUB_TOKEN` environment variable. You can try using it to log in to GHCR without creating a separate personal access token:

```
echo $GITHUB_TOKEN | docker login ghcr.io -u $GITHUB_USER --password-stdin
```

You should see `Login Succeeded`.

If the login succeeds but the push in step 3 fails with a `permission_denied` or
`denied: installation not allowed to Create organization package` error, the
codespace token is not allowed to publish packages. In that case:

1. On GitHub, go to **Settings** → **Developer settings** → **Personal access tokens**
   → **Tokens (classic)** → **Generate new token (classic)**
2. Give it a short expiration and select the `write:packages` scope
3. Copy the token and log in with it instead (the `read -s` command hides what
   you paste so it doesn't end up in your terminal history):

```
read -s CR_PAT
echo $CR_PAT | docker login ghcr.io -u $GITHUB_USER --password-stdin
```

### 2. Tag the image with the GHCR format

Docker requires images destined for a registry to be tagged with the full registry path before they can be pushed. The format for GHCR is:

```
ghcr.io/<your-github-username>/<image-name>:<tag>
```

Tag the `python_script` image you built earlier (run this from anywhere; tagging
does not depend on your current directory):

```
docker tag python_script:latest ghcr.io/<your-github-username>/python_script:latest
```

Confirm the new tag appears alongside the original with `docker images`. Notice
that both rows have the same IMAGE ID. A tag is just another name pointing to the
same image, not a copy.

### 3. Push the image

```
docker push ghcr.io/<your-github-username>/python_script:latest
```

Docker uploads each layer individually and prints a digest when the push completes. Layers that already exist in the registry are skipped — this is the same caching mechanism you saw during `docker build`.

### 4. Make the package public

Newly pushed GHCR packages are private by default. To make yours pullable without authentication:

1. Go to your GitHub profile → **Packages** tab
2. Click `python_script`
3. Click **Package settings** (right side of the page)
4. Scroll to the **Danger Zone** → **Change visibility** → **Public**, and type
   the package name to confirm

### 5. Verify the push

Remove your local copies of the image so Docker is forced to pull from the registry,
then pull it back and run it. You will need to remove any containers made from
`python_script` first (see `docker ps -a`), for example `docker rm test1`.

```
docker rmi ghcr.io/<your-github-username>/python_script:latest python_script:latest
docker pull ghcr.io/<your-github-username>/python_script:latest
docker run --name from_registry ghcr.io/<your-github-username>/python_script:latest
```

You should see the same GC content output as before — the image running from the registry is identical to the one you built locally.

This is exactly the workflow used to build and distribute the course containers. When you run Nextflow with `-profile singularity`, Nextflow pulls from `ghcr.io/bf528/` and Singularity converts the Docker image into a `.sif` file it can run on the cluster.

## Commonly used commands

### Building an image from the Dockerfile in the current directory
```
docker build -t <image_name>:<tag> .
```

### Running a container from an image
```
docker run --name <container_name> <image_name>
```

### Running a container interactively - (-i | --interactive) and (-t | --tty)
```
docker run -it <image_name> bash
```

From the Docker documentation: The -i flag is most often used together with the 
-t flag to bind the I/O streams of the container to a pseudo terminal, creating 
an interactive terminal session for the container.

### Running a container with a bind mount
```
docker run --volume $(pwd):/app --name <container_name> <image_name>
```

### Listing all containers (including stopped ones)
```
docker ps -a
```

### Removing a container
```
docker rm <container_name>
```

### Listing all images
```
docker images
```

### Removing an image
```
docker rmi <image_name>:<tag>
```

### Tagging and pushing an image to GHCR
```
docker tag <image_name>:latest ghcr.io/<your-github-username>/<image_name>:latest
docker push ghcr.io/<your-github-username>/<image_name>:latest
```
