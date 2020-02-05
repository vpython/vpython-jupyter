# How to do a vpython release

There are two things that need to be released:

+ The Python package `vpython-jupyter`
+ The JupyterLab extension called `vpython`

## Releasing the Python package

Versions for the Python package are generated using
[`versioneer`](https://github.com/warner/python-versioneer). That means that
to make a new release the first step is to generate a git tag with the release
numbers.

Release numbers should be in the format `X.Y.Z`, e.g. `7.4.2` or `7.5.0`.

Currently, all of the build/upload of the releases is handled on Travis-CI and
Appveyor, but in principle one could build the packages on local machines and
upload them.

Tagging the commit in GitHub or doing the tag locally and pushing it to GitHub
will trigger the builds without any further action.

If you want to build locally:

+ Build and upload the source distribution (once per release)
    * `python setup.py sdist` -- generate the source distribution
    * `twine upload dist/*.tar.gz` -- upload the generated distribution
+ Build and upload binary wheels (once per release *per platform*)
    * `python setup.py wheel` -- generate binary distribution on the platform
      on which you are running.
    * `twine upload dist/*.whl` -- upload the generated distribution
+ Build the conda package (once per release *per platform*)
    * `conda build vpython.recipe`
    * `anaconda upload `*recipe_location* -- replace *recipe_location* with
      the directory output by conda build.

## Releasing the JupyterLab Extension

Please see the instructions in the `labextension` folder for building and
releasing the JupyterLab extension.
