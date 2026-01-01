import bisect
import re
from typing import AbstractSet, List, Mapping, Optional, Sequence, Tuple

from typing_extensions import TypedDict

from zulint.printer import BLUE, ENDC, GREEN, MAGENTA, YELLOW, colors, print_err


class Rule(TypedDict, total=False):
    bad_lines: Sequence[str]
    description: str
    exclude: AbstractSet[str]
    exclude_line: AbstractSet[Tuple[str, str]]
    exclude_pattern: str
    good_lines: Sequence[str]
    include_only: AbstractSet[str]
    pattern: str


class RuleList:
    """Defines and runs custom linting rules for the specified language."""

    def __init__(
        self,
        langs: Sequence[str],
        rules: Sequence[Rule],
        exclude_files_in: Optional[str] = None,
    ) -> None:
        self.langs = langs
        self.rules = rules
        # Exclude the files in this folder from rules
        self.exclude_files_in = "\\"
        self.verbose = False

    def get_rules_applying_to_fn(self, fn: str, rules: Sequence[Rule]) -> List[Rule]:
        rules_to_apply = []
        for rule in rules:
            excluded = False
            for item in rule.get("exclude", set()):
                if fn.startswith(item):
                    excluded = True
                    break
            if excluded:
                continue
            if rule.get("include_only"):
                found = False
                for item in rule.get("include_only", set()):
                    if item in fn:
                        found = True
                if not found:
                    continue
            rules_to_apply.append(rule)

        return rules_to_apply

    def check_file_for_pattern(
        self,
        fn: str,
        contents: str,
        line_starts: Sequence[int],
        identifier: str,
        color: str,
        rule: Rule,
    ) -> bool:
        """
        DO NOT MODIFY THIS FUNCTION WITHOUT PROFILING.

        This function gets called ~40k times, once per file per regex.

        DO NOT INLINE THIS FUNCTION.

        We need to see it show up in profiles, and the function call
        overhead will never be a bottleneck.
        """
        exclude_lines = {
            line
            for (exclude_fn, line) in rule.get("exclude_line", set())
            if exclude_fn == fn
        }
        unmatched_exclude_lines = exclude_lines.copy()

        ok = True
        for m in re.finditer(rule["pattern"], contents, re.M):
            i = bisect.bisect(line_starts, m.start()) - 1
            line = contents[
                line_starts[i] : line_starts[i + 1]
                if i + 1 < len(line_starts)
                else None
            ]
            line_fully_stripped = line.strip()
            if line_fully_stripped in exclude_lines:
                unmatched_exclude_lines.discard(line_fully_stripped)
                continue
            if rule.get("exclude_pattern") and re.search(
                rule["exclude_pattern"], line_fully_stripped
            ):
                continue
            self.print_error(rule, line, identifier, color, fn, i + 1)
            ok = False

        if unmatched_exclude_lines:
            print("Please remove exclusions for file {fn}: {unmatched_exclude_lines}")

        return ok

    def print_error(
        self,
        rule: Rule,
        line: str,
        identifier: str,
        color: str,
        fn: str,
        line_number: int,
    ) -> None:
        print_err(
            identifier,
            color,
            "{} {}at {} line {}:".format(
                YELLOW + rule["description"], BLUE, fn, line_number
            ),
        )
        print_err(identifier, color, line)
        if self.verbose:
            if rule.get("good_lines"):
                print_err(
                    identifier,
                    color,
                    GREEN
                    + "  Good code: {}{}".format(
                        (YELLOW + " | " + GREEN).join(rule["good_lines"]), ENDC
                    ),
                )
            if rule.get("bad_lines"):
                print_err(
                    identifier,
                    color,
                    MAGENTA
                    + "  Bad code:  {}{}".format(
                        (YELLOW + " | " + MAGENTA).join(rule["bad_lines"]), ENDC
                    ),
                )
            print_err(identifier, color, "")

    def custom_check_file(
        self,
        fn: str,
        identifier: str,
        color: str,
    ) -> bool:
        failed = False

        with open(fn, encoding="utf8") as f:
            contents = f.read()
        line_starts = [m.start() for m in re.finditer(r"^.", contents, re.M | re.S)]

        rules_to_apply = self.get_rules_applying_to_fn(fn=fn, rules=self.rules)

        for rule in rules_to_apply:
            ok = self.check_file_for_pattern(
                fn=fn,
                contents=contents,
                line_starts=line_starts,
                identifier=identifier,
                color=color,
                rule=rule,
            )
            if not ok:
                failed = True

        return failed

    def check(
        self, by_lang: Mapping[str, Sequence[str]], verbose: bool = False
    ) -> bool:
        # By default, a rule applies to all files within the extension for
        # which it is specified (e.g. all .py files)
        # There are three operators we can use to manually include or exclude files from linting for a rule:
        # 'exclude': 'set([<path>, ...])' - if <path> is a filename, excludes that file.
        #                                   if <path> is a directory, excludes all files
        #                                   directly below the directory <path>.
        # 'exclude_line': 'set([(<path>, <line>), ...])' - excludes all lines matching <line>
        #                                                  in the file <path> from linting.
        # 'include_only': 'set([<path>, ...])' - includes only those files where <path> is a
        #                                        substring of the filepath.
        failed = False
        self.verbose = verbose
        for lang in self.langs:
            color = next(colors)
            for fn in by_lang[lang]:
                if fn.startswith(self.exclude_files_in) or ("custom_check.py" in fn):
                    # This is a bit of a hack, but it generally really doesn't
                    # work to check the file that defines all the things to check for.
                    #
                    # TODO: Migrate this to looking at __module__ type attributes.
                    continue
                if self.custom_check_file(fn, lang, color):
                    failed = True

        return failed
