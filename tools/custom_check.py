from __future__ import print_function
from __future__ import absolute_import

from typing import cast, Any, Dict, List, Tuple
from zulint.custom_rules import RuleList

Rule = List[Dict[str, Any]]

whitespace_rules = [
    # This linter should be first since bash_rules depends on it.
    {'pattern': '\s+$',
     'strip': '\n',
     'description': 'Fix trailing whitespace'},
    {'pattern': '\t',
     'strip': '\n',
     'description': 'Fix tab-based whitespace'},
]  # type: Rule

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
]  # type: Rule

python_rules = RuleList(
    langs=['py'],
    rules=cast(Rule, [
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
    ]) + whitespace_rules,
    max_length=140,
)

bash_rules = RuleList(
    langs=['sh'],
    rules=cast(Rule, [
        {'pattern': '#!.*sh [-xe]',
         'description': 'Fix shebang line with proper call to /usr/bin/env for Bash path, change -x|-e switches'
                        ' to set -x|set -e'},
    ]) + whitespace_rules[0:1],
)


json_rules = RuleList(
    langs=['json'],
    # Here, we don't check tab-based whitespace, because the tab-based
    # whitespace rule flags a lot of third-party JSON fixtures
    # under zerver/webhooks that we want preserved verbatim.  So
    # we just include the trailing whitespace rule and a modified
    # version of the tab-based whitespace rule (we can't just use
    # exclude in whitespace_rules, since we only want to ignore
    # JSON files with tab-based whitespace, not webhook code).
    rules= whitespace_rules[0:1],
)

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
]  # type: Rule

markdown_docs_length_exclude = {
    "zulip_bots/zulip_bots/bots/converter/doc.md",
    "tools/server_lib/README.md",
}

markdown_rules = RuleList(
    langs=['md'],
    rules=markdown_whitespace_rules + prose_style_rules + cast(Rule, [
        {'pattern': '\[(?P<url>[^\]]+)\]\((?P=url)\)',
         'description': 'Linkified markdown URLs should use cleaner <http://example.com> syntax.'}
    ]),
    max_length=120,
    length_exclude=markdown_docs_length_exclude,
)

txt_rules = RuleList(
    langs=['txt'],
    rules=whitespace_rules,
)

non_py_rules = [
    json_rules,
    markdown_rules,
    bash_rules,
    txt_rules,
]
