#!/usr/bin/env python

import os
from setuptools import setup, find_packages

import genre_expand


def read(*names):
    values = dict()
    extensions = ['.txt', '.rst']
    for name in names:
        value = ''
        for extension in extensions:
            filename = name + extension
            if os.path.isfile(filename):
                value = open(name + extension).read()
                break
        values[name] = value
    return values


long_description = """
%(README)s

News
====

%(CHANGES)s

""" % read('README', 'CHANGES')

setup(
    name='genre_expand',
    version=genre_expand.__version__,
    description='expand ID3 genre metadata',
    long_description=long_description,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Topic :: Utilities",
    ],
    keywords='expand id3 mp3 genre metadata wikipedia eyed3 music tag',
    author='Hunter Hammond',
    author_email='huntrar@gmail.com',
    maintainer='Hunter Hammond',
    maintainer_email='huntrar@gmail.com',
    url='https://github.com/huntrar/genre-expand',
    license='MIT',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'genre-expand = genre_expand.genre-expand:command_line_runner',
        ]
    },
    install_requires=[
        'eyed3',
        'six',
        'wikipedia'
    ]
)
