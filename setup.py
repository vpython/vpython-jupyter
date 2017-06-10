from __future__ import print_function

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

install_requires = ['jupyter', 'vpnotebook', 'numpy']

if sys.version_info.major == 3 and sys.version_info.minor >= 5:
    install_requires.append('autobahn')

setup(
    name='vpython',
    packages=['vpython'],
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    description='VPython for Jupyter Notebook',
    long_description=open('README.md').read(),
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
    package_data={'vpython': ['vpython_data/*', 'vpython_libraries/*']},
)
