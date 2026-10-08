# slim images usually refer to images that have had non-essential
# packages and libraries removed in order to reduce the image size
FROM python:slim-bullseye

# workdir will set the provided path as the working directory
WORKDIR /script

# copies files from the build context (the directory) into the image
COPY requirements.txt .

# Uses pip to install the package we want
RUN pip install --no-cache-dir -r requirements.txt

# Copies the script and file into the image
COPY script.py genomeC.fna .

# The CMD to run by default when a container starts from the image
CMD ["python", "script.py"]