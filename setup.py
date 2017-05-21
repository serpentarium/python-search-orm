#!/usr/bin/env python

from os import path
from sys import version_info, exit
from setuptools import setup, find_packages

py_version = version_info[:2]
if py_version <= (3, 3):
    print('Requires Python version 3.3 or later, ({}.{} detected).'
          .format(*py_version))
    exit(1)

try:
    import pso
except ImportError:
    print('Cannot access module, is the source tree broken?')
    exit(1)

here = path.abspath(path.dirname(__file__))
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='search-orm',
    version=pso.__version__,
    description="Unified ORM for lucene based search engines.",
    long_description=long_description,
    url='https://github.com/serpentarium/python-search-orm',
    author='ubombi',
    author_email='ubombi@gmail.com',
    license='MIT',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
    ],
    keywords='orm search',
    packages=find_packages(exclude=['tests']),
    install_requires=[],
    extras_require={
        # 'dev': [''],
        'test': ['nose'],
    },
)
