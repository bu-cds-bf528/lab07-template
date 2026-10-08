# Don't change this - this is installing a base image with conda installed
FROM continuumio/miniconda3

# Set the workdir to /app


# Add your code here to make it work
# You will need to make the YML file and fq file available in the container


# You will then need to create a conda environment with the correct name


# Don't change this either (need to activate environment and add it to path)
# Note the name of the environment
RUN echo "source activate fastqc_env" > ~/.bashrc
ENV PATH=/opt/conda/envs/fastqc_env/bin:$PATH

# Add CMD here to run fastqc
CMD ["fastqc", "example.fq.gz"]