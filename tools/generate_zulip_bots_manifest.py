#!/usr/bin/env python

import os
import glob

def get_zulip_bots_test_fixtures():
    # type: () -> List[str]
    current_dir = os.path.abspath(os.path.dirname(__file__))
    bots_dir = os.path.join(current_dir, '..', 'zulip_bots/zulip_bots/bots')
    glob_pattern = os.path.join(bots_dir, '*/fixtures/*.json')
    fixtures_paths = map(
        lambda fp: os.path.join(*fp.split('/')[-5:]),
        glob.glob(glob_pattern)
    )
    return fixtures_paths

def get_zulip_bots_logos():
    # type: () -> List[str]
    current_dir = os.path.abspath(os.path.dirname(__file__))
    bots_dir = os.path.join(current_dir, '..', 'zulip_bots/zulip_bots/bots')
    glob_pattern = os.path.join(bots_dir, '*/logo.*')
    logo_paths = map(
        lambda fp: os.path.join(*fp.split('/')[-4:]),
        glob.glob(glob_pattern)
    )
    return logo_paths

def get_zulip_bots_docs():
    # type: () -> List[str]
    current_dir = os.path.abspath(os.path.dirname(__file__))
    bots_dir = os.path.join(current_dir, '..', 'zulip_bots/zulip_bots/bots')
    glob_pattern = os.path.join(bots_dir, '*/doc.md')
    doc_paths = map(
        lambda fp: os.path.join(*fp.split('/')[-4:]),
        glob.glob(glob_pattern)
    )
    return doc_paths

def main():
    # type: () -> None
    current_dir = os.path.abspath(os.path.dirname(__file__))
    manifest_path = os.path.join(current_dir, '..', 'zulip_bots/MANIFEST.in')

    with open(manifest_path, 'w') as fp:
        template = 'include {line}\n'
        fixtures = map(lambda line: template.format(line=line),
                       get_zulip_bots_test_fixtures())
        logos = map(lambda line: template.format(line=line),
                    get_zulip_bots_logos())
        docs = map(lambda line: template.format(line=line),
                   get_zulip_bots_docs())

        fp.writelines(fixtures)
        fp.write('\n')

        fp.writelines(logos)
        fp.write('\n')

        fp.writelines(docs)
        fp.write('\n')

if __name__ == '__main__':
    main()
