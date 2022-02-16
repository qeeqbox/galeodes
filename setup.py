#!/usr/bin/python
# -*- coding: utf-8 -*-

from setuptools import setup

with open("README.rst", "r") as f:
    long_description = f.read()

setup(
    name='galeodes',
    author='QeeqBox',
    author_email='gigaqeeq@gmail.com',
    description="Browsers options",
    long_description=long_description,
    version='0.6',
    license='AGPL-3.0',
    url='https://github.com/qeeqbox/galeodes',
    packages=['galeodes'],
    install_requires=[
        'selenium',
        'requests',
        'Pillow'
    ],
    python_requires='>=3.5',
    entry_points={
        "console_scripts": [
            'galeodes=galeodes.__main__:main_logic'
        ]
    }
)
