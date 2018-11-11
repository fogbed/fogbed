#!/usr/bin/env python

"Setuptools params"

from setuptools import setup, find_packages
from os.path import join

# Get version number from source tree
import sys
from src import __fogbed_version__
sys.path.append( '.' )

scripts = [ join( 'bin', filename ) for filename in [ 'mn' ] ]

modname = distname = 'fogbed'

setup(
    name=distname,
    version=__fogbed_version__,
    description='Containernet fork that add Fogbed support.',
    author='Heitor Rodrigues',
    author_email='hr.heitor@hotmail.com',
    packages=find_packages(),
    long_description="""
        Mininet is a network emulator which uses lightweight
        virtualization to create virtual networks for rapid
        prototyping of Software-Defined Network (SDN) designs
        using OpenFlow. http://mininet.org
        Mininet author: Bob Lantz (rlantz@cs.stanford.edu)
 
        Containernet is a fork of Mininet that allows
        to use Docker containers as hosts in emulated
        networks.
        """,
    classifiers=[
          "License :: OSI Approved :: BSD License",
          "Programming Language :: Python",
          "Development Status :: 5 - Production/Stable",
          "Intended Audience :: Developers",
          "Topic :: System :: Emulators",
    ],
    keywords='networking emulator protocol Internet OpenFlow SDN fog',
    license='BSD',
    install_requires=[
        'setuptools',
        'urllib3',
        'ipaddress',
        'docker==3.4.0',
        'python-iptables',
        'pytest',
        'Pyro4'
    ],
    include_package_data=True,
    package_data={
        "src.maxinet":["Scripts/*"],
      },
    entry_points={
        'console_scripts': [
            'FogbedWorker = src.maxinet.WorkerServer.server:main',
            'FogbedFrontendServer = src.maxinet.FrontendServer.server:main',
            'FogbedStatus = src.maxinet.WorkerServer.server:getFrontendStatus',
        ]
      },
    scripts=scripts,
)
