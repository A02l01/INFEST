# Installing INFEST

## Prerequisites

INFEST needs these python packages to work.

- scikit-image
- numpy
- scipy
- pandas
- matplotlib

These can be installed using either [conda](https://docs.conda.io/en/latest/) or [pip](https://pip.pypa.io/en/stable/).


If you want to plot animations of the leaves, you'll also need the [ffmpeg](https://ffmpeg.org/) tool installed.
On ubuntu/debian this can be installed with:

```
sudo apt update && sudo apt install ffmpeg
```

Alternatively you can use conda.

Both of the installation options described below also require git.


## Using Conda

Install conda
- For linux install please see: [here](https://docs.conda.io/projects/conda/en/latest/user-guide/install/linux.html)
- For other systems: [here](https://docs.conda.io/projects/conda/en/latest/user-guide/install/#system-requirements)

A conda environment contains all of the software you need for a specific task (or set of tasks), in a folder that you can easily create, destroy, load and unload as you like.
This makes it easy to use different versions of software etc.

To create an environment you can run the following:

```
curl -o environment.yml https://raw.githubusercontent.com/darcyabjones/INFEST/master/environment.yaml

conda env create -f environment.yml -n INFEST
conda activate INFEST

# OR 

conda env create -f environment.yml -p ./condaenv
conda activate ./condaenv
```

The difference is that with `-n` you can load the environment from anywhere (but files are always stored in your home directory), whereas with `-p` you can specify where the files are kept.
On supercomputers or other places where your home disk space is small, the `-p` option is often better.

Any time you want to use the program after restarting your terminal, you'll need to run the appropriate `conda activate` command as above.


> Advanced users may wish to investigate [mamba](https://github.com/mamba-org/mamba) and [micromamba](https://mamba.readthedocs.io/en/latest/user_guide/micromamba.html).
> These are faster alternatives to conda and the commands above are completely compatible, just replace `conda` with `mamba` and you should be good to go.


## Using pip

Pip will usually come installed with any new python installation.
But if it isn't available, you can install it on debian/ubuntu with:

```
sudo apt update && sudo apt install python3-pip
```

> NOTE: on some operating systems you may need to substitute `python3` for `python` (e.g. some new linux versions), or `Python` (Windows CMD).

I highly recommend that you install the program into a virtual environment of some kind.
This avoids compatibility issues with other software.

```
python3 -m venv ./env 
source ./env/bin/activate

python3 -m pip install git+https://github.com/darcyabjones/INFEST.git
```

To use the virtual environment in the future, you'll need to run `source ./env/bin/activate` whenever you re-start the terminal.


If you don't want to use a virtual environment, it's better to install as user (rather than a whole system installation).

```
python3 -m pip install --user git+https://github.com/darcyabjones/INFEST.git
```

You may then need to add that directory to your `PATH`. e.g.

```
# The directory may be different, but this is fairly common on linux.
echo 'export PATH="${PATH:-}:${HOME}/.local/bin"' >> ~/.bashrc
```


## Using pip, without git

If you don't have git installed (and can't install it), you can install it like this:

```
# OPTIONAL but recommended
# Create a conda or virtualenv

# You could also do this with a browser if you prefer.
curl -o INFEST.zip https://github.com/darcyabjones/INFEST/archive/refs/heads/master.zip
unzip INFEST.zip

# Or with --user
# If you want to be able to edit the package and have changes work immediately you can also specify `-e` or `--editable`
python3 -m pip install ./INFEST/
```
