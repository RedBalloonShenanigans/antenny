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
        "colorama",
        "mpfshell==0.9.1"
        "pyserial",
        "rbs-tui-dom",
        "websocket_client",
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