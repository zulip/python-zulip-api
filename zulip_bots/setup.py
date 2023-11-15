from setuptools import find_packages, setup

ZULIP_BOTS_VERSION = "0.9.0"
IS_PYPA_PACKAGE = False


package_data = {
    "": ["doc.md", "*.conf", "assets/*"],
    "zulip_bots": ["py.typed"],
}

# IS_PYPA_PACKAGE should be set to True before making a PyPA release.
if not IS_PYPA_PACKAGE:
    package_data[""].append("fixtures/*.json")
    package_data[""].append("logo.*")

with open("README.md") as fh:
    long_description = fh.read()

setup(
    name="zulip_bots",
    version=ZULIP_BOTS_VERSION,
    description="Zulip's Bot framework",
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
    entry_points={
        "console_scripts": [
            "zulip-run-bot=zulip_bots.run:main",
            "zulip-bot-shell=zulip_bots.bot_shell:main",
        ],
    },
    install_requires=[
        "pip",
        "zulip",
        "html2text",
        "lxml",
        "BeautifulSoup4",
        "typing_extensions>=4.5.0",
        'importlib-metadata >= 3.6; python_version  < "3.10"',
    ],
    packages=find_packages(),
    package_data=package_data,
)
