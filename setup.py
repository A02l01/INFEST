"""A setuptools based setup module.
See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path
from glob import glob
from os.path import (basename, dirname, splitext)

here = path.abspath(dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='INFEST',

    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # https://packaging.python.org/en/latest/single_source_version.html
    version='0.9.1',

    description='INFEST for kINematic oF lESion developmenT',
    long_description=long_description,
    long_description_content_type="text/markdown",

    # The project's main homepage.
    url='https://github.com/A02l01/INFEST',

    # Author details
    author='Adelin Barbacci',
    author_email='adelin.barbacci@inrae.fr',

    # Choose your license
    license='MIT',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 4 - Beta',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: Apache Software License',

        # Specify the Python versions you support here.
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],

    # What does your project relate to?
    keywords='fungi machine-learning phenotyping',

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    packages=find_packages("src"),
    package_dir={'': 'src'},

    # List run-time dependencies here.  These will be installed by pip when
    # your project is installed. For an analysis of "install_requires" vs pip's
    # requirements files see:
    # https://packaging.python.org/en/latest/requirements.html

    # Sorry about the hard dependency for scikit-learn.
    # The way that the PCA model is stored is not necessarily stable across
    # versions of scikit-learn, so I have to keep it fixed.
    install_requires=[
        'scikit-image',
        'scikit-learn',
        'numpy',
        'scipy',
        'pandas',
        'matplotlib',
        'Pillow'
        ],
    py_modules=[splitext(basename(path))[0] for path in glob('src/*.py')],

    # List additional groups of dependencies here (e.g. development
    # dependencies). You can install these using the following syntax,
    # for example:
    # $ pip install -e .[dev,test]
    extras_require={
        'dev': ['check-manifest', 'scipy', 'scikit-learn',
                'jupyter', 'matplotlib', 'seaborn', "pandas"],
        'test': ['coverage', 'pytest', 'mypy', 'types-setuptools'],
    },

    # If there are data files included in your packages that need to be
    # installed, specify them here.  If using Python 2.6 or less, then these
    # have to be included in MANIFEST.in as well.
    #package_data={
    #    'INFEST': ['data/*.json', 'data/*.tsv', 'data/*.csv', 'data/*.txt'],
    #},
    include_package_data=True,

    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # pip to create the appropriate form of executable for the target platform.
    entry_points={
        'console_scripts': [
            'infest=INFEST.__main__:main',
            'infest-quant=INFEST.quant:main',
            'infest-check-layout=INFEST.check_layout:main',
            'infest-norm=INFEST.norm_colours:main',
            'infest-example=INFEST.example_data:main',
            'infest-predict=INFEST.gompertz:main'
        ],
    },
)
