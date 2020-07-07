#!/usr/bin/env python
from setuptools import setup

from mp import version

setup(
    name="nyanshell",
    version="0.0.1",
    description="The nyansat project Micropython devices.",
    author="Red Balloon Security",
    url="https://github.com/RedBalloonShenanigans/antenny/",
    install_requires=[
        "pyserial",
        "colorama",
        "websocket_client",
        "mpfshell==0.9.1"
    ],
    keywords=["micropython", ],
    classifiers=[],
    entry_points={
        "console_scripts": [
            "nyanui=host:main",
            "nyanshell=host.shell:main",
        ]
    },
)