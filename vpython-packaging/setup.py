from distutils.core import setup

try:
    from vpnotebook import cmdclass
except:
    import pip, importlib
    pip.main(['install', 'vpython']); cmdclass = importlib.import_module('vpnotebook').cmdclass

setup(
    name='vpython',
    packages=['vpython','vpnotebook'],
    version='0.1.0a3',
    description='VPython for Jupyter Notebook',
    long_description=open('README.txt').read(),
    author='Bruce Sherwood',
    author_email='bruce.sherwood@gmail.com',
    url='http://pypi.python.org/pypi/vpython/',
    license='LICENSE.txt',
    keywords='vpython',
    classifiers=[
          'Framework :: IPython',
          'Development Status :: 3 - Alpha',
          'Environment :: Web Environment',
          'Intended Audience :: End Users/Desktop',
          'Natural Language :: English',
          'Programming Language :: Python',
          'Topic :: Multimedia :: Graphics :: 3D Modeling',
          'Topic :: Multimedia :: Graphics :: 3D Rendering',
          'Topic :: Scientific/Engineering :: Visualization',
    ],
    install_requires=['vpython'],
    cmdclass=cmdclass('vpnotebook/data'),
    package_data={'vpython': ['data/*'],
                  'vpnotebook': ['data/kernel.json']},
    
)