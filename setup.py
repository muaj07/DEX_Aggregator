#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open("README.md") as readme_file:
    readme = readme_file.read()

with open("HISTORY.rst") as history_file:
    history = history_file.read()

requirements = [
    "Click>=7.0",
]

test_requirements = [
    "pytest>=3",
]

setup(
    author="Jimmy Shen",
    author_email="jmmshn@gmail.com",
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    description="ENTROPIC DEXA",
    entry_points={
        "console_scripts": [
            "entropic=entropic.cli:main",
        ],
    },
    install_requires=requirements,
    long_description=readme + "\n\n" + history,
    include_package_data=True,
    keywords="entropic",
    name="entropic",
    packages=find_packages(include=["entropic", "entropic.*"]),
    test_suite="tests",
    tests_require=test_requirements,
    url="https://github.com/jmmshn/entropic",
    version="0.1.0",
    zip_safe=False,
)
