from __future__ import print_function
from __future__ import absolute_import

import os
import re
import traceback

from server_lib.printer import print_err, colors

from typing import cast, Any, Callable, Dict, List, Optional, Tuple

def build_custom_checkers(by_lang):
    # type: (Dict[str, List[str]]) -> Tuple[Callable[[], bool], Callable[[], bool]]
    RuleList = List[Dict[str, Any]]

    def custom_check_file(fn, identifier, rules, skip_rules=None, max_length=None):
        # type: (str, str, RuleList, Optional[Any], Optional[int]) -> bool
        failed = False
        color = next(colors)

        line_tups = []
        for i, line in enumerate(open(fn)):
            line_newline_stripped = line.strip('\n')
            line_fully_stripped = line_newline_stripped.strip()
            skip = False
            for rule in skip_rules or []:
                if re.match(rule, line):
                    skip = True
            if line_fully_stripped.endswith('  # nolint'):
                continue
            if skip:
                continue
            tup = (i, line, line_newline_stripped, line_fully_stripped)
            line_tups.append(tup)

        rules_to_apply = []
        fn_dirname = os.path.dirname(fn)
        for rule in rules:
            exclude_list = rule.get('exclude', set())
            if fn in exclude_list or fn_dirname in exclude_list:
                continue
            if rule.get("include_only"):
                found = False
                for item in rule.get("include_only", set()):
                    if item in fn:
                        found = True
                if not found:
                    continue
            rules_to_apply.append(rule)

        for rule in rules_to_apply:
            exclude_lines = {
                line for
                (exclude_fn, line) in rule.get('exclude_line', set())
                if exclude_fn == fn
            }

            pattern = rule['pattern']
            for (i, line, line_newline_stripped, line_fully_stripped) in line_tups:
                if line_fully_stripped in exclude_lines:
                    exclude_lines.remove(line_fully_stripped)
                    continue
                try:
                    line_to_check = line_fully_stripped
                    if rule.get('strip') is not None:
                        if rule['strip'] == '\n':
                            line_to_check = line_newline_stripped
                        else:
                            raise Exception("Invalid strip rule")
                    if re.search(pattern, line_to_check):
                        print_err(identifier, color, '{} at {} line {}:'.format(
                            rule['description'], fn, i+1))
                        print_err(identifier, color, line)
                        failed = True
                except Exception:
                    print("Exception with %s at %s line %s" % (rule['pattern'], fn, i+1))
                    traceback.print_exc()

            if exclude_lines:
                print('Please remove exclusions for file %s: %s' % (fn, exclude_lines))

        lastLine = None
        for (i, line, line_newline_stripped, line_fully_stripped) in line_tups:
            if isinstance(line, bytes):
                line_length = len(line.decode("utf-8"))
            else:
                line_length = len(line)
            if (max_length is not None and line_length > max_length and
                '# type' not in line and 'test' not in fn and 'example' not in fn and
                not re.match("\[[ A-Za-z0-9_:,&()-]*\]: http.*", line) and
                not re.match("`\{\{ external_api_uri_subdomain \}\}[^`]+`", line) and
                    "#ignorelongline" not in line and 'migrations' not in fn):
                print("Line too long (%s) at %s line %s: %s" % (len(line), fn, i+1, line_newline_stripped))
                failed = True
            lastLine = line

        if lastLine and ('\n' not in lastLine):
            print("No newline at the end of file.  Fix with `sed -i '$a\\' %s`" % (fn,))
            failed = True

        return failed

    whitespace_rules = [
        # This linter should be first since bash_rules depends on it.
        {'pattern': '\s+$',
         'strip': '\n',
         'description': 'Fix trailing whitespace'},
        {'pattern': '\t',
         'strip': '\n',
         'description': 'Fix tab-based whitespace'},
    ]  # type: RuleList
    markdown_whitespace_rules = list([rule for rule in whitespace_rules if rule['pattern'] != '\s+$']) + [
        # Two spaces trailing a line with other content is okay--it's a markdown line break.
        # This rule finds one space trailing a non-space, three or more trailing spaces, and
        # spaces on an empty line.
        {'pattern': '((?<!\s)\s$)|(\s\s\s+$)|(^\s+$)',
         'strip': '\n',
         'description': 'Fix trailing whitespace'},
        {'pattern': '^#+[A-Za-z0-9]',
         'strip': '\n',
         'description': 'Missing space after # in heading'},
    ]  # type: RuleList
    python_rules = cast(RuleList, [
        {'pattern': '".*"%\([a-z_].*\)?$',
         'description': 'Missing space around "%"'},
        {'pattern': "'.*'%\([a-z_].*\)?$",
         'description': 'Missing space around "%"'},
        # This rule is constructed with + to avoid triggering on itself
        {'pattern': " =" + '[^ =>~"]',
         'description': 'Missing whitespace after "="'},
        {'pattern': '":\w[^"]*$',
         'description': 'Missing whitespace after ":"'},
        {'pattern': "':\w[^']*$",
         'description': 'Missing whitespace after ":"'},
        {'pattern': "^\s+[#]\w",
         'strip': '\n',
         'description': 'Missing whitespace after "#"'},
        {'pattern': "assertEquals[(]",
         'description': 'Use assertEqual, not assertEquals (which is deprecated).'},
        {'pattern': 'self: Any',
         'description': 'you can omit Any annotation for self',
         'good_lines': ['def foo (self):'],
         'bad_lines': ['def foo(self: Any):']},
        {'pattern': "== None",
         'description': 'Use `is None` to check whether something is None'},
        {'pattern': "type:[(]",
         'description': 'Missing whitespace after ":" in type annotation'},
        {'pattern': "# type [(]",
         'description': 'Missing : after type in type annotation'},
        {'pattern': "#type",
         'description': 'Missing whitespace after "#" in type annotation'},
        {'pattern': 'if[(]',
         'description': 'Missing space between if and ('},
        {'pattern': ", [)]",
         'description': 'Unnecessary whitespace between "," and ")"'},
        {'pattern': "%  [(]",
         'description': 'Unnecessary whitespace between "%" and "("'},
        # This next check could have false positives, but it seems pretty
        # rare; if we find any, they can be added to the exclude list for
        # this rule.
        {'pattern': ' % [a-zA-Z0-9_.]*\)?$',
         'description': 'Used % comprehension without a tuple'},
        {'pattern': '.*%s.* % \([a-zA-Z0-9_.]*\)$',
         'description': 'Used % comprehension without a tuple'},
        # This rule might give false positives in virtualenv setup files which should be excluded,
        # and comments which should be rewritten to avoid use of "python2", "python3", etc.
        {'pattern': 'python[23]',
         'include_only': set(['zulip/']),
         'description': 'Explicit python invocations should not include a version'},
        {'pattern': '__future__',
         'include_only': set(['zulip_bots/zulip_bots/bots/']),
         'description': 'Bots no longer need __future__ imports.'},
        {'pattern': '#!/usr/bin/env python$',
         'include_only': set(['zulip_bots/']),
         'description': 'Python shebangs must be python3'},
        {'pattern': '(^|\s)open\s*\(',
         'description': 'open() should not be used in Zulip\'s bots. Use functions'
                        ' provided by the bots framework to access the filesystem.',
         'include_only': set(['zulip_bots/zulip_bots/bots/'])},
        {'pattern': 'pprint',
         'description': 'Used pprint, which is most likely a debugging leftover. For user output, use print().'},
        {'pattern': '\(BotTestCase\)',
         'bad_lines': ['class TestSomeBot(BotTestCase):'],
         'description': 'Bot test cases should directly inherit from BotTestCase *and* DefaultTests.'},
        {'pattern': '\(DefaultTests, BotTestCase\)',
         'bad_lines': ['class TestSomeBot(DefaultTests, BotTestCase):'],
         'good_lines': ['class TestSomeBot(BotTestCase, DefaultTests):'],
         'description': 'Bot test cases should inherit from BotTestCase before DefaultTests.'},
    ]) + whitespace_rules
    bash_rules = [
        {'pattern': '#!.*sh [-xe]',
         'description': 'Fix shebang line with proper call to /usr/bin/env for Bash path, change -x|-e switches'
                        ' to set -x|set -e'},
    ] + whitespace_rules[0:1]  # type: RuleList
    prose_style_rules = [
        {'pattern': '[^\/\#\-\"]([jJ]avascript)',  # exclude usage in hrefs/divs
         'description': "javascript should be spelled JavaScript"},
        {'pattern': '[^\/\-\.\"\'\_\=\>]([gG]ithub)[^\.\-\_\"\<]',  # exclude usage in hrefs/divs
         'description': "github should be spelled GitHub"},
        {'pattern': '[oO]rganisation',  # exclude usage in hrefs/divs
         'description': "Organization is spelled with a z"},
        {'pattern': '!!! warning',
         'description': "!!! warning is invalid; it's spelled '!!! warn'"},
        {'pattern': '[^-_]botserver(?!rc)|bot server',
         'description': "Use Botserver instead of botserver or Botserver."},
    ]  # type: RuleList
    json_rules = []  # type: RuleList # fix newlines at ends of files
    # It is okay that json_rules is empty, because the empty list
    # ensures we'll still check JSON files for whitespace.
    markdown_rules = markdown_whitespace_rules + prose_style_rules + [
        {'pattern': '\[(?P<url>[^\]]+)\]\((?P=url)\)',
         'description': 'Linkified markdown URLs should use cleaner <http://example.com> syntax.'}
    ]
    help_markdown_rules = markdown_rules + [
        {'pattern': '[a-z][.][A-Z]',
         'description': "Likely missing space after end of sentence"},
        {'pattern': '[rR]ealm',
         'description': "Realms are referred to as Organizations in user-facing docs."},
    ]
    txt_rules = whitespace_rules

    def check_custom_checks_py():
        # type: () -> bool
        failed = False

        for fn in by_lang['py']:
            if 'custom_check.py' in fn:
                continue
            if custom_check_file(fn, 'py', python_rules, max_length=140):
                failed = True
        return failed

    def check_custom_checks_nonpy():
        # type: () -> bool
        failed = False

        for fn in by_lang['sh']:
            if custom_check_file(fn, 'sh', bash_rules):
                failed = True

        for fn in by_lang['json']:
            if custom_check_file(fn, 'json', json_rules):
                failed = True

        markdown_docs_length_exclude = {
            "zulip_bots/zulip_bots/bots/converter/doc.md",
            "tools/server_lib/README.md",
        }
        for fn in by_lang['md']:
            max_length = None
            if fn not in markdown_docs_length_exclude:
                max_length = 120
            rules = markdown_rules
            if fn.startswith("templates/zerver/help"):
                rules = help_markdown_rules
            if custom_check_file(fn, 'md', rules, max_length=max_length):
                failed = True

        for fn in by_lang['txt'] + by_lang['text']:
            if custom_check_file(fn, 'txt', txt_rules):
                failed = True

        for fn in by_lang['yaml']:
            if custom_check_file(fn, 'yaml', txt_rules):
                failed = True

        return failed

    return (check_custom_checks_py, check_custom_checks_nonpy)
