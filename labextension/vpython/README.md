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

but taylor the instructions for creating a vpython labextension.

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


