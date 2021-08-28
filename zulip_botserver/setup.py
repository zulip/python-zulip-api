#!/usr/bin/env python3

import sys
from typing import Any, Dict, Optional

ZULIP_BOTSERVER_VERSION = "0.8.0"

with open("README.md") as fh:
    long_description = fh.read()

# We should be installable with either setuptools or distutils.
package_info = dict(
    name="zulip_botserver",
    version=ZULIP_BOTSERVER_VERSION,
    description="Zulip's Flask server for running bots",
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
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    python_requires=">=3.6",
    url="https://www.zulip.org/",
    project_urls={
        "Source": "https://github.com/zulip/python-zulip-api/",
        "Documentation": "https://zulip.com/api",
    },
    entry_points={
        "console_scripts": [
            "zulip-botserver=zulip_botserver.server:main",
        ],
    },
    test_suite="tests",
    package_data={"zulip_botserver": ["py.typed"]},
)  # type: Dict[str, Any]

setuptools_info = dict(
    install_requires=[
        "zulip",
        "zulip_bots",
        "flask>=0.12.2",
    ],
)

try:
    from setuptools import find_packages, setup

    package_info.update(setuptools_info)
    package_info["packages"] = find_packages(exclude=["tests"])

except ImportError:
    from distutils.core import setup
    from distutils.version import LooseVersion
    from importlib import import_module

    # Manual dependency check
    def check_dependency_manually(module_name: str, version: Optional[str] = None) -> None:
        try:
            module = import_module(module_name)  # type: Any
            if version is not None:
                assert LooseVersion(module.__version__) >= LooseVersion(version)
        except (ImportError, AssertionError):
            if version is not None:
                print(
                    f"{module_name}>={version} is not installed.",
                    file=sys.stderr,
                )
            else:
                print(f"{module_name} is not installed.", file=sys.stderr)
            sys.exit(1)

    check_dependency_manually("zulip")
    check_dependency_manually("zulip_bots")
    check_dependency_manually("flask", "0.12.2")

    package_info["packages"] = ["zulip_botserver"]


setup(**package_info)
