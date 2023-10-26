#!/usr/bin/env python3

import itertools
import os
from typing import Any, Generator, List, Tuple

from setuptools import find_packages, setup

with open("README.md") as fh:
    long_description = fh.read()


def version() -> str:
    version_py = os.path.join(os.path.dirname(__file__), "zulip", "__init__.py")
    with open(version_py) as in_handle:
        version_line = next(
            itertools.dropwhile(lambda x: not x.startswith("__version__"), in_handle)
        )
    version = version_line.split("=")[-1].strip().replace('"', "")
    return version


def recur_expand(target_root: Any, dir: Any) -> Generator[Tuple[str, List[str]], None, None]:
    for root, _, files in os.walk(dir):
        paths = [os.path.join(root, f) for f in files]
        if len(paths):
            yield os.path.join(target_root, root), paths


setup(
    name="zulip",
    version=version(),
    description="Bindings for the Zulip message API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Zulip Open Source Project",
    author_email="zulip-devel@googlegroups.com",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Topic :: Communications :: Chat",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    url="https://www.zulip.org/",
    project_urls={
        "Source": "https://github.com/zulip/python-zulip-api/",
        "Documentation": "https://zulip.com/api",
    },
    data_files=list(recur_expand("share/zulip", "integrations")),
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "zulip-send=zulip.send:main",
            "zulip-api-examples=zulip.api_examples:main",
            "zulip-matrix-bridge=integrations.bridge_with_matrix.matrix_bridge:main",
            "zulip-api=zulip.cli:cli",
        ],
    },
    install_requires=[
        "requests[security]>=0.12.1",
        "distro",
        "click",
        "typing_extensions>=4.5.0",
    ],
    packages=find_packages(exclude=["tests"]),
)
