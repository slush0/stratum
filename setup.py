#!/usr/bin/env python
from distribute_setup import use_setuptools
use_setuptools()

from setuptools import setup

setup(name='Stratum',
      version='0.1',
      description='Stratum server implementation based on Twisted',
      author='slush',
      author_email='info@bitcion.cz',
      url='http://stratum.bitcoin.cz',
      packages=['stratum',],
      install_requires=['twisted', 'ecdsa', 'pyopenssl', 'autobahn',]# 'Twisted%20Words'],
     )
