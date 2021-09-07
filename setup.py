#!/usr/bin/env python
from setuptools import setup


setup(
    name="pymyenergi",
    version="0.0.11",
    author="Johan Isaksson",
    author_email="johan@generatorhallen.se",
    description="Python library and CLI for communicating with myenergi API.",
    include_package_data=True,
    url="https://github.com/cjne/pymyenergi",
    license="MIT",
    packages=["pymyenergi"],
    python_requires=">=3.6",
    install_requires=["httpx"],
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Operating System :: OS Independent",
    ],
    setup_requires=("pytest-runner"),
    tests_require=(
        "asynctest",
        "pytest-cov",
        "pytest-asyncio",
        "pytest-trio",
        "pytest-tornasync",
    ),
)
