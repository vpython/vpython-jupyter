import sys

try:
    from setuptools import setup  # try first in case it's already there.
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup

from distutils.extension import Extension

try:
    from Cython.Build import cythonize
    USE_CYTHON = True
    extensions = cythonize('vpython/cyvector.pyx')
except ImportError:
    extensions = [Extension('vpython.cyvector', ['vpython/cyvector.c'])]

import versioneer

install_requires = ['jupyter', 'jupyter-server-proxy', 'numpy', 'ipykernel',
                    'autobahn>=18.8.2']

setup_args = dict(
    name='vpython',
    packages=['vpython'],
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
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
    ext_modules=extensions,
    install_requires=install_requires,
    python_requires=">=3.7",
    package_data={'vpython': ['vpython_data/*',
                              'vpython_libraries/*',
                              'vpython_libraries/images/*']},
)

try:
    setup(**setup_args)
except SystemExit as e:
    print('Compiled version of vector failed with:')
    print(e)
    print('***** Using pure python version of vector, which is slower.')

    # Do not try to build the extension
    del setup_args['ext_modules']
    setup(**setup_args)
