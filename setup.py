from __future__ import print_function
try:
    from setuptools import setup
except:
    print("no setuptools, using distutils")
    from distutils.core import setup

setup(
    name='vpython',
    packages=['vpython'],
    version='0.2.0b3',
    description='VPython for Jupyter Notebook',
    long_description=open('README.md').read(),
    author='John Coady / Ruth Chabay / Bruce Sherwood',
    author_email='bruce.sherwood@gmail.com',
    url='http://pypi.python.org/pypi/vpython/',
    license='LICENSE.txt',
    keywords='vpython',
    classifiers=[
          'Framework :: IPython',
          'Development Status :: 4 - Beta',
          'Environment :: Web Environment',
          'Intended Audience :: End Users/Desktop',
          'Natural Language :: English',
          'Programming Language :: Python',
          'Topic :: Multimedia :: Graphics :: 3D Modeling',
          'Topic :: Multimedia :: Graphics :: 3D Rendering',
          'Topic :: Scientific/Engineering :: Visualization',
    ],
    install_requires=['jupyter', 'vpnotebook'],
    package_data={'vpython': ['data/*']},
)
