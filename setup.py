#!/usr/bin/env python
from distribute_setup import use_setuptools
use_setuptools()

#python setup.py sdist upload

from setuptools import setup

setup(name='stratum',
      version='0.2.8',
      description='Stratum server implementation based on Twisted',
      author='slush',
      author_email='info@bitcion.cz',
      url='http://stratum.bitcoin.cz',
      packages=['stratum',],
      py_modules=['distribute_setup',],
      zip_safe=False,
      install_requires=['twisted', 'ecdsa', 'pyopenssl', 'autobahn',]
     )
