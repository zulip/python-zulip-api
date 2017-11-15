#!/usr/bin/env python

import argparse
import os
import glob
import distutils.cmd
import distutils.log
if False:
    from typing import IO, Iterator

CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))
BOTS_DIR = os.path.normpath(os.path.join(CURRENT_DIR, 'zulip_bots', 'bots'))
MANIFEST_PATH = os.path.join(CURRENT_DIR, 'MANIFEST.in')

class GenerateManifest(distutils.cmd.Command):
    """
    A custom setup.py command to generate a MANIFEST.in
    for the zulip_bots package.
    """
    description = 'generate a MANIFEST.in for PyPA or for development'
    user_options = [
        ('release', None, 'generate a MANIFEST for a PyPA release'),
    ]

    def initialize_options(self):
        # type: () -> None
        self.release = False

    def finalize_options(self):
        # type: () -> None
        pass

    def run(self):
        # type: () -> None
        if self.release:
            generate_release_manifest()
            self.announce(  # type: ignore # https://github.com/zulip/python-zulip-api/issues/142
                'Generating a MANIFEST for a PyPA release of zulip_bots.',
                level=distutils.log.INFO  # type: ignore # https://github.com/zulip/python-zulip-api/issues/142
            )
        else:
            generate_dev_manifest()
            self.announce(  # type: ignore # https://github.com/zulip/python-zulip-api/issues/142
                'Generating a MANIFEST for zulip_bots\' development.',
                level=distutils.log.INFO  # type: ignore # https://github.com/zulip/python-zulip-api/issues/142
            )

def get_test_fixtures():
    # type: () -> Iterator[str]
    glob_pattern = os.path.join(BOTS_DIR, '*', 'fixtures', '*.json')
    fixtures_paths = map(
        lambda fp: os.path.join(*fp.split(os.path.sep)[-5:]).replace(os.path.sep, '/'),
        glob.glob(glob_pattern)
    )
    return fixtures_paths

def get_logos():
    # type: () -> Iterator[str]
    glob_pattern = os.path.join(BOTS_DIR, '*', 'logo.*')
    logo_paths = map(
        lambda fp: os.path.join(*fp.split(os.path.sep)[-4:]).replace(os.path.sep, '/'),
        glob.glob(glob_pattern)
    )
    return logo_paths

def get_docs():
    # type: () -> Iterator[str]
    glob_pattern = os.path.join(BOTS_DIR, '*', 'doc.md')
    doc_paths = map(
        lambda fp: os.path.join(*fp.split(os.path.sep)[-4:]).replace(os.path.sep, '/'),
        glob.glob(glob_pattern)
    )
    return doc_paths

def get_assets():
    # type: () -> Iterator[str]
    glob_pattern = os.path.join(BOTS_DIR, '*', 'assets', '*')
    assets_files = map(
        lambda fp: os.path.join(*fp.split(os.path.sep)[-5:]).replace(os.path.sep, '/'),
        glob.glob(glob_pattern)
    )
    return assets_files

def generate_and_write(filepaths, file_obj):
    # type: (Iterator[str], IO[str]) -> None
    template = 'include {line}\n'
    lines = map(lambda line: template.format(line=line), filepaths)

    file_obj.writelines(lines)
    file_obj.write('\n')

def generate_dev_manifest():
    # type: () -> None
    with open(MANIFEST_PATH, 'w') as fp:
        generate_and_write(get_test_fixtures(), fp)
        generate_and_write(get_logos(), fp)
        generate_and_write(get_docs(), fp)
        generate_and_write(get_assets(), fp)

def generate_release_manifest():
    # type: () -> None
    with open(MANIFEST_PATH, 'w') as fp:
        generate_and_write(get_docs(), fp)
        generate_and_write(get_assets(), fp)

def parse_args():
    # type: () -> argparse.Namespace
    usage = """
To generate a MANIFEST.in for a PyPA release, run:

./generate_manifest.py --release

To generate a MANIFEST.in for development, run without arguments:

./generate_manifest.py
"""
    parser = argparse.ArgumentParser(usage=usage)

    parser.add_argument('--release', '-r',
                        action='store_true',
                        default=False,
                        help='Generate MANIFEST.in for a PyPA release.')

    return parser.parse_args()

def main():
    # type: () -> None
    options = parse_args()
    if options.release:
        generate_release_manifest()
    else:
        generate_dev_manifest()


if __name__ == '__main__':
    main()
