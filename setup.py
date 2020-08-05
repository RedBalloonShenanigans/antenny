#!/usr/bin/env python
from setuptools import setup


setup(
    name="nyansat",
    version="0.0.1",
    description="The nyansat project Micropython devices.",
    author="Red Balloon Security",
    url="https://github.com/RedBalloonShenanigans/antenny/",
    install_requires=[
        "aiohttp",
        "colorama",
        "fuzzywuzzy",
        "mpfshell==0.9.1",
        "pyserial",
        "rbs-tui-dom",
        "skyfield",
        "websocket_client",
        "python-Levenshtein",
        "mpfshell",
        "dataclasses",
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
