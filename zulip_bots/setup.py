#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import sys

# Before anything, generate MANIFEST.in
import generate_manifest
generate_manifest.main()

# We should be installable with either setuptools or distutils.
package_info = dict(
    name='zulip_bots',
    version='0.3.3',
    description='Zulip\'s Bot framework',
    author='Zulip Open Source Project',
    author_email='zulip-devel@googlegroups.com',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Topic :: Communications :: Chat',
    ],
    url='https://www.zulip.org/',
    entry_points={
        'console_scripts': [
            'zulip-run-bot=zulip_bots.run:main',
            'zulip-bot-output=zulip_bots.zulip_bot_output:main'
        ],
    },
    include_package_data=True,
)  # type: Dict[str, Any]

setuptools_info = dict(
    install_requires=[
        'zulip>=0.3.3',
        'mock>=2.0.0',
        'html2text',  # for bots/define
    ],
)

try:
    from setuptools import setup, find_packages
    package_info.update(setuptools_info)
    package_info['packages'] = find_packages()

except ImportError:
    from distutils.core import setup
    from distutils.version import LooseVersion
    from importlib import import_module

    # Manual dependency check
    def check_dependency_manually(module_name, version=None):
        try:
            module = import_module(module_name)
            if version is not None:
                assert(LooseVersion(module.__version__) >= LooseVersion(version))
        except (ImportError, AssertionError):
            if version is not None:
                print("{name}>={version} is not installed.".format(
                    req=req, version=version), file=sys.stderr)
            else:
                print("{name} is not installed.".format(name=module_name), file=sys.stderr)
            sys.exit(1)

    check_dependency_manually('zulip', '0.3.3')
    check_dependency_manually('mock', '2.0.0')
    check_dependency_manually('html2text')
    check_dependency_manually('PyDictionary')

    # Include all submodules under bots/
    package_list = ['zulip_bots']
    dirs = os.listdir('zulip_bots/bots/')
    for dir_name in dirs:
        if os.path.isdir(os.path.join('zulip_bots/bots/', dir_name)):
            package_list.append('zulip_bots.bots.' + dir_name)
    package_info['packages'] = package_list


setup(**package_info)
