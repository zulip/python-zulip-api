#!/usr/bin/env python

import os
import glob

CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))
BOTS_DIR = os.path.normpath(os.path.join(CURRENT_DIR, 'zulip_bots', 'bots'))

def get_test_fixtures():
    # type: () -> List[str]
    glob_pattern = os.path.join(BOTS_DIR, '*', 'fixtures', '*.json')
    fixtures_paths = map(
        lambda fp: os.path.join(*fp.split(os.path.sep)[-5:]).replace(os.path.sep, '/'),
        glob.glob(glob_pattern)
    )
    return fixtures_paths

def get_logos():
    # type: () -> List[str]
    glob_pattern = os.path.join(BOTS_DIR, '*', 'logo.*')
    logo_paths = map(
        lambda fp: os.path.join(*fp.split(os.path.sep)[-4:]).replace(os.path.sep, '/'),
        glob.glob(glob_pattern)
    )
    return logo_paths

def get_docs():
    # type: () -> List[str]
    glob_pattern = os.path.join(BOTS_DIR, '*', 'doc.md')
    doc_paths = map(
        lambda fp: os.path.join(*fp.split(os.path.sep)[-4:]).replace(os.path.sep, '/'),
        glob.glob(glob_pattern)
    )
    return doc_paths

def main():
    # type: () -> None
    manifest_path = os.path.join(CURRENT_DIR, 'MANIFEST.in')
    with open(manifest_path, 'w') as fp:
        template = 'include {line}\n'
        fixtures = map(lambda line: template.format(line=line),
                       get_test_fixtures())
        logos = map(lambda line: template.format(line=line),
                    get_logos())
        docs = map(lambda line: template.format(line=line),
                   get_docs())

        fp.writelines(fixtures)
        fp.write('\n')

        fp.writelines(logos)
        fp.write('\n')

        fp.writelines(docs)
        fp.write('\n')

if __name__ == '__main__':
    main()
