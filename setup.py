import os

from setuptools import setup

from distutils.extension import Extension

# Set VPYTHON_PURE_PYTHON=1 to build with no C extension at all. The result is a
# `py3-none-any` wheel, which is what Pyodide/micropip and other wasm targets
# require — they cannot install a platform wheel, and declaring `ext_modules` is
# what makes every wheel a platform wheel.
#
# Nothing is lost but speed: `_vector_import_helper` already falls back to the
# pure-Python `vector` implementation when `cyvector` cannot be imported, so the
# same source runs either way. Ordinary builds are unchanged — this is opt-in.
PURE_PYTHON = os.environ.get('VPYTHON_PURE_PYTHON', '').strip() not in ('', '0', 'false', 'False')

if PURE_PYTHON:
    extensions = []
else:
    try:
        from Cython.Build import cythonize
        USE_CYTHON = True
        extensions = cythonize('vpython/cyvector.pyx')
    except ImportError:
        extensions = [Extension('vpython.cyvector', ['vpython/cyvector.c'])]


install_requires = ['jupyter', 'jupyter-server-proxy', 'jupyterlab-vpython>=3.1.8', 'notebook>=7.0.0', 'numpy', 'ipykernel',
                    'autobahn>=22.6.1, <27']

setup_args = dict(
    name='vpython',
    packages=['vpython'],
    description='VPython for Jupyter Notebook',
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    author='John Coady / Ruth Chabay / Bruce Sherwood / Steve Spicklemire',
    author_email='bruce.sherwood@gmail.com',
    url='http://pypi.python.org/pypi/vpython/',
    license='LICENSE.txt',
    keywords='vpython',
    classifiers=[
          'Framework :: IPython',
          'Development Status :: 5 - Production/Stable',
          'Environment :: Web Environment',
          'Intended Audience :: End Users/Desktop',
          'Natural Language :: English',
          'Programming Language :: Python',
          'Topic :: Multimedia :: Graphics :: 3D Modeling',
          'Topic :: Multimedia :: Graphics :: 3D Rendering',
          'Topic :: Scientific/Engineering :: Visualization',
    ],
    install_requires=install_requires,
    python_requires=">=3.8",   # importlib.metadata, used in vpython/__init__.py
    package_data={'vpython': ['vpython_data/*',
                              'vpython_libraries/*',
                              'vpython_libraries/images/*']},
)

# `ext_modules` is added only for a normal build. Omitting the key entirely (as
# opposed to passing an empty list) is what makes setuptools tag the wheel
# `py3-none-any` rather than a platform wheel.
if not PURE_PYTHON:
    setup_args['ext_modules'] = extensions

try:
    setup(**setup_args)
except SystemExit as e:
    print('Compiled version of vector failed with:')
    print(e)
    print('***** Using pure python version of vector, which is slower.')

    # Do not try to build the extension
    del setup_args['ext_modules']
    setup(**setup_args)
