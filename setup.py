#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name='pycycles',
    version='0.1.0',
    description='Python API client to find rent cycles from local cycle service',
    url='http://github.com/dan-ess/pycycles',
    author='dan',
    author_email='',
    license='MIT',
    packages=['pycycles'],
    install_requires=['requests-html'],
    python_requires='>=3.6.0',
)
