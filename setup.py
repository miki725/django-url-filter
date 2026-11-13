#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
import os

from setuptools import find_packages, setup

from url_filter import __author__, __version__


def read(fname):
    with open(os.path.join(os.path.dirname(__file__), fname), "rb") as fid:
        return fid.read().decode("utf-8")


authors = read("AUTHORS.rst")
history = read("HISTORY.rst").replace(".. :changelog:", "")
licence = read("LICENSE.rst")
readme = read("README.rst")

req = read("requirements.txt").splitlines()
dev_req = read("requirements-dev.txt").splitlines()[2:]

requirements = req + ["setuptools"]
test_requirements = req + dev_req

setup(
    name="dj-url-filter",
    version=__version__,
    author=__author__,
    description="Django URL Filter provides a safe way to filter data via human-friendly URLs.",
    long_description="\n\n".join([readme, history, authors, licence]),
    url="https://github.com/miki725/dj-url-filter",
    license="MIT",
    packages=find_packages(exclude=["test_project*", "tests*"]),
    install_requires=requirements,
    python_requires=">=3.13",
    test_suite="tests",
    tests_require=test_requirements,
    keywords=" ".join(["django django-rest-framework"]),
    classifiers=[
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Framework :: Django",
        "Framework :: Django :: 5.2",
        "Framework :: Django :: 6.0",
        "Framework :: Django :: 6.1",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "Programming Language :: Python :: 3.15",
        "Development Status :: 2 - Pre-Alpha",
    ],
)
