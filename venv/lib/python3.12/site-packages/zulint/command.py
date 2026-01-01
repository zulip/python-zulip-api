import argparse
import logging
import multiprocessing
import sys
import time
import weakref
from typing import Callable, Dict, List, Mapping, NoReturn, Sequence, Set, Tuple, Union

from zulint import lister
from zulint.linters import run_command
from zulint.printer import BLUE, BOLDRED, ENDC, GREEN, colors


def add_default_linter_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--modified", "-m", action="store_true", help="Only check modified files"
    )
    parser.add_argument(
        "--verbose-timing",
        "-vt",
        action="store_true",
        help="Print verbose timing output",
    )
    parser.add_argument("targets", nargs="*", help="Specify directories to check")
    parser.add_argument(
        "--skip",
        default=[],
        type=split_arg_into_list,
        help="Specify linters to skip, eg: --skip=mypy,gitlint",
    )
    parser.add_argument(
        "--only",
        default=[],
        type=split_arg_into_list,
        help="Specify linters to run, eg: --only=mypy,gitlint",
    )
    parser.add_argument(
        "--list", "-l", action="store_true", help="List all the registered linters"
    )
    parser.add_argument(
        "--list-groups",
        "-lg",
        action="store_true",
        help="List all the registered linter groups",
    )
    parser.add_argument(
        "--groups",
        "-g",
        default=[],
        type=split_arg_into_list,
        help="Only run linter for languages in the group(s), e.g.: "
        "--groups=backend,frontend",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print verbose output where available",
    )
    parser.add_argument(
        "--fix", action="store_true", help="Automatically fix problems where supported"
    )
    parser.add_argument("--jobs", "-j", type=int, help="Limit number of parallel jobs")


def split_arg_into_list(arg: str) -> List[str]:
    return arg.split(",")


run_parallel_functions: "weakref.WeakValueDictionary[int, Callable[[], int]]" = (
    weakref.WeakValueDictionary()
)


def run_parallel_worker(item: Tuple[str, int]) -> Tuple[str, int]:
    name, func_id = item
    func = run_parallel_functions[func_id]
    logging.info("start %s", name)
    time_start = time.perf_counter()
    result = func()
    time_end = time.perf_counter()
    logging.info("finish %s; elapsed time: %g", name, time_end - time_start)
    sys.stdout.flush()
    sys.stderr.flush()
    return name, result


def run_parallel(
    lint_functions: Mapping[str, Callable[[], int]], jobs: int
) -> Set[str]:
    # Smuggle the functions through a global variable to work around
    # multiprocessing's inability to pickle closures.
    for func in lint_functions.values():
        run_parallel_functions[id(func)] = func

    failed_linters = set()
    args = ((name, id(func)) for name, func in lint_functions.items())
    if jobs != 1 and multiprocessing.get_start_method() == "fork":
        with multiprocessing.Pool(jobs) as pool:
            for name, result in pool.imap_unordered(run_parallel_worker, args):
                if result != 0:
                    failed_linters.add(name)
    else:
        for name, result in map(run_parallel_worker, args):
            if result != 0:
                failed_linters.add(name)
    return failed_linters


class LinterConfig:
    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args
        self.by_lang: Dict[str, List[str]] = {}
        self.groups: Mapping[str, Sequence[str]] = {}
        self.lint_functions: Dict[str, Callable[[], int]] = {}
        self.lint_descriptions: Dict[str, str] = {}
        self.fixable_linters: Set[str] = set()

    def list_files(
        self,
        file_types: Sequence[str] = [],
        groups: Mapping[str, Sequence[str]] = {},
        use_shebang: bool = True,
        exclude: Sequence[str] = [],
    ) -> Dict[str, List[str]]:
        assert (
            file_types or groups
        ), "Atleast one of `file_types` or `groups` must be specified."

        self.groups = groups
        if self.args.groups:
            file_types = [ft for group in self.args.groups for ft in groups[group]]
        else:
            file_types = [
                *file_types,
                *{ft for group in groups.values() for ft in group},
            ]

        self.by_lang = lister.list_files(
            targets=self.args.targets,
            modified_only=self.args.modified,
            ftypes=file_types,
            use_shebang=use_shebang,
            group_by_ftype=True,
            exclude=exclude,
        )
        return self.by_lang

    def lint(self, func: Callable[[], int]) -> Callable[[], int]:
        self.lint_functions[func.__name__] = func
        self.lint_descriptions[func.__name__] = (
            func.__doc__ if func.__doc__ else "External Linter"
        )
        return func

    def external_linter(
        self,
        name: str,
        command: Sequence[str],
        target_langs: Sequence[str] = [],
        pass_targets: bool = True,
        fix_arg: Union[str, Sequence[str]] = [],
        description: str = "External Linter",
        check_arg: Union[str, Sequence[str]] = [],
        suppress_line: Callable[[str], bool] = lambda line: False,
    ) -> None:
        """Registers an external linter program to be run as part of the
        linter.  This program will be passed the subset of files being
        linted that have extensions in target_langs.  If there are no
        such files, exits without doing anything.

        If target_langs is empty, just runs the linter unconditionally.
        """
        self.lint_descriptions[name] = description
        if fix_arg or check_arg:
            self.fixable_linters.add(name)
        color = next(colors)

        def run_linter() -> int:
            targets: List[str] = []
            if len(target_langs) != 0:
                targets = [
                    target for lang in target_langs for target in self.by_lang[lang]
                ]
                if len(targets) == 0:
                    # If this linter has a list of languages, and
                    # no files in those languages are to be checked,
                    # then we can safely return success without
                    # invoking the external linter.
                    return 0

            full_command = list(command)
            arg = fix_arg if self.args.fix else check_arg
            full_command += [arg] if isinstance(arg, str) else arg

            if pass_targets:
                full_command += targets

            return run_command(name, color, full_command, suppress_line)

        self.lint_functions[name] = run_linter

    def set_logger(self) -> None:
        logging.basicConfig(format="%(asctime)s %(message)s")
        logger = logging.getLogger()
        if self.args.verbose_timing:
            logger.setLevel(logging.INFO)
        else:
            logger.setLevel(logging.WARNING)

    def do_lint(self) -> NoReturn:
        assert (
            not self.args.only or not self.args.skip
        ), "Only one of --only or --skip can be used at once."
        if self.args.only:
            self.lint_functions = {
                linter: self.lint_functions[linter] for linter in self.args.only
            }
        for linter in self.args.skip:
            del self.lint_functions[linter]
        if self.args.list:
            print("{}{:<15} {} {}".format(BOLDRED, "Linter", "Description", ENDC))
            for linter, desc in self.lint_descriptions.items():
                print(f"{BLUE}{linter:<15} {GREEN}{desc}{ENDC}")
            sys.exit()
        if self.args.list_groups:
            print("{}{:<15} {} {}".format(BOLDRED, "Linter Group", "File types", ENDC))
            for group, file_types in self.groups.items():
                print(
                    "{}{:<15} {}{}{}".format(
                        BLUE, group, GREEN, ", ".join(file_types), ENDC
                    )
                )
            sys.exit()
        self.set_logger()

        jobs = self.args.jobs
        if self.args.fix:
            # Do not run multiple fixers in parallel, since they might
            # race with each other and corrupt each other's output.
            jobs = 1

        failed_linters = run_parallel(self.lint_functions, jobs)

        failed_fixable_linters = failed_linters & self.fixable_linters
        if failed_fixable_linters:
            print(
                "Run {}{} --fix{} to fix errors for the following linters: {}".format(
                    BLUE, sys.argv[0], ENDC, ",".join(sorted(failed_fixable_linters))
                ),
            )

        sys.exit(1 if failed_linters else 0)
