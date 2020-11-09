# vpython

VPython labextension


## Prerequisites

* JupyterLab ^0.35.0
* VPython Package >=7.4.8     (pip install vpython) or (conda install -c vpython vpython)

## Installation

```bash
jupyter labextension install vpython
```

## Development

For a development install use the instructions for creating a custom jupyter labextension as a guide:

https://jupyterlab.readthedocs.io/en/stable/developer/extension_tutorial.html#extension-tutorial

Except where the tutorial says: `conda install -c conda-forge jupyterlab=2`, use `jupyterlab=1`
and tailor the instructions for creating a vpython labextension. Also, the tutorial command
`jupyter lab --watch` will fail. Just use `jupyter lab`.

The original instructions below caused trouble for me (steve, I got various React errors) but this is what worked:

1) Create and activate a conda environment, and then install jupyterlab:

    conda create -n jupyterlab-ext --override-channels --strict-channel-priority -c conda-forge -c anaconda jupyterlab cookiecutter nodejs git

    conda activate jupyterlab-ext

    conda install -c conda-forge jupyterlab=1

2) git clone the repository (the branch from the pull request) somewhere using whatever git machinery you prefer.

Then “cd” into the ‘vpython-jupyter/labextension/vpython’ of that repository.

3) In the ‘vpython-jupyter/labextension/vpython’ directory of that repository execute:

    cp -r ../../vpython/vpython_{libraries,data} .

    yarn install

    jupyter labextension install .

4) Install vpyton in this virtual environment:

   cd ../..

   pip install -e .
   
And then to run a lab notebook:

    jupyter lab

Then you should be able to import vpython now and run notebooks in jupyterlab.

Original instructions:

```bash
jlpm install
jlpm add @jupyterlab/application
jlpm add @jupyterlab/apputils
jlpm add @jupyterlab/coreutils
jlpm add @jupyterlab/docregistry
jlpm add @jupyterlab/notebook
jlpm add @phosphor/disposable
jlpm add script-loader

cp -r ../../vpython/vpython_{libraries,data} .
jlpm run build
jupyter labextension install .
```

To rebuild the package and the JupyterLab app:

```bash
jlpm run build
jupyter lab build
```
