#!/usr/bin/env python
#python setup.py sdist upload

from setuptools import setup
from stratum import version

setup(name='stratum',
      version=version.VERSION,
      description='Stratum server implementation based on Twisted',
      author='slush',
      author_email='info@bitcion.cz',
      url='http://blog.bitcoin.cz/stratum',
      packages=['stratum',],
      zip_safe=False,
      install_requires=['twisted', 'ecdsa', 'autobahn',]
     )
