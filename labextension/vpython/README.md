# jupyterlab_vpython

A VPython extension for JupyterLab

## Requirements

- JupyterLab >= 3.0.0
- VPython >= 7.6.4

## Install

To install the extension, execute:

```bash
pip install jupyterlab_vpython
```

## Uninstall

To remove the extension, execute:

```bash
pip uninstall jupyterlab_vpython
```

## Development

For a development install use the instructions for creating a custom jupyter labextension as a guide:

https://jupyterlab.readthedocs.io/en/latest/extension/extension_tutorial.html

Follow the steps in the tutorial

Step 1:

```bash
conda create -n jupyterlab-ext --override-channels --strict-channel-priority -c conda-forge -c nodefaults jupyterlab=4 nodejs=18 git copier=7 jinja2-time
```

Step 2:

```bash
conda activate jupyterlab-ext
```

Step 3: Get the jupyterlab_vpython repository

```bash
git clone https://github.com/jcoady/jupyterlab_vpython.git
```

Step 4:

```bash
cd jupyterlab_vpython
```

Step 5:
```bash
jlpm install
jlpm add @jupyterlab/application
jlpm add @jupyterlab/apputils
jlpm add @jupyterlab/coreutils
jlpm add @jupyterlab/docregistry
jlpm add @jupyterlab/notebook
jlpm add @lumino/disposable
jlpm add file-loader
jlpm add plotly.js-dist-min
jlpm add script-loader

cp -r ../../vpython/vpython_{libraries,data} .
jlpm run build
```

Step 6: install the extension into the JupyterLab environment.

```bash
pip install -ve .
```

Step 7: After the install completes, open a second terminal. 
Run these commands to activate the jupyterlab-ext environment 
and start JupyterLab in your default web browser.

```bash
conda activate jupyterlab-ext
jupyter lab
```

Step 8: Packaging the extension.

Before generating a package, we first need to install build.

```bash
pip install build
```

To create a Python source package (.tar.gz) in the dist/ directory, do:

```bash
python -m build -s
```

To create a Python wheel package (.whl) in the dist/ directory, do:

```bash
python -m build
```
