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

For a development install (requires npm version 4 or later), do the following in the repository directory:

```bash
npm install
cp -r ../../vpython/vpython_{libraries,data} lib/
jupyter labextension install .
```

To rebuild the package and the JupyterLab app:

```bash
npm run build
jupyter lab build
```

