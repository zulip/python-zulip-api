#!/usr/bin/env python3

from setuptools import find_packages, setup

ZULIP_BOTSERVER_VERSION = "0.8.2"

with open("README.md") as fh:
    long_description = fh.read()

setup(
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
    install_requires=[
        "zulip",
        "zulip_bots",
        "flask>=0.12.2",
    ],
    packages=find_packages(exclude=["tests"]),
)
