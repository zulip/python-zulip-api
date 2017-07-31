#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import sys

# We should be installable with either setuptools or distutils.
package_info = dict(
    name='zulip_botserver',
    version='0.3.2',
    description='Zulip\'s Flask server for running bots',
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
            'zulip-bot-server=zulip_botserver.server:main',
        ],
    },
    test_suite='tests',
)  # type: Dict[str, Any]

setuptools_info = dict(
    install_requires=[
        'zulip>=0.3.1',
        'zulip_bots>=0.3.1',
        'flask>=0.12.2',
    ],
)

try:
    from setuptools import setup, find_packages
    package_info.update(setuptools_info)
    package_info['packages'] = find_packages(exclude=['tests'])

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

    check_dependency_manually('zulip', '0.3.1')
    check_dependency_manually('zulip_bots', '0.3.1')
    check_dependency_manually('flask', '0.12.2')

    package_info['packages'] = ['zulip_botserver']


setup(**package_info)
