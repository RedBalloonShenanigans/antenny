#!/usr/bin/env python
from setuptools import setup

from mp import version

setup(
    name="nyanshell",
    version=version.FULL,
    description="A shell for Antenny project"
    "Micropython devices.",
    author="Red Balloon Security",
    url="https://github.com/RedBalloonShenanigans/antenny/",
    install_requires=["pyserial", "colorama", "websocket_client", "mpfshell==0.9.1"],
    keywords=["micropython", "shell", "file transfer", "development"],
    classifiers=[],
    entry_points={"console_scripts": ["nyanshell=nyanshell:main"]},
)
