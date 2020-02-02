# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

import os


package_dir = os.path.dirname(os.path.abspath(__file__))
version = open(os.path.join(package_dir, "VERSION")).read().strip()
readme = open(os.path.join(package_dir, "README.md")).read().strip()

setup(
    name="panel-components",
    version=version,
    author="Paulo Lopes",
    author_email="paulopes00@gmail.com",
    url="https://github.com/paulopes/panel-components",
    description="HTML components for Panel templates.",
    long_description=readme,
    packages=find_packages("panel_components"),
    install_requires=["panel"],
    test_suite="tests",
)
