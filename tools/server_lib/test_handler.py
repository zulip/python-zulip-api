from importlib import import_module

import os
import sys
import argparse
import unittest
import pytest
import shutil

TOOLS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(TOOLS_DIR))

def handle_input_and_run_tests_for_package(package_name, path_list):
    parser = argparse.ArgumentParser(description="Run tests for {}.".format(package_name))
    parser.add_argument('--coverage',
                        nargs='?',
                        const=True,
                        default=False,
                        help='compute test coverage (--coverage combine to combine with previous reports)')
    parser.add_argument('--pytest', '-p',
                        default=False,
                        action='store_true',
                        help="run tests with pytest")
    parser.add_argument('--verbose', '-v',
                        default=False,
                        action='store_true',
                        help='show verbose output (with pytest)')
    options = parser.parse_args()

    test_session_title = ' Running tests for {} '.format(package_name)
    header = test_session_title.center(shutil.get_terminal_size().columns, '#')
    print(header)

    if options.coverage:
        import coverage
        cov = coverage.Coverage(config_file="tools/.coveragerc")
        if options.coverage == 'combine':
            cov.load()
        cov.start()

    if options.pytest:
        location_to_run_in = os.path.join(TOOLS_DIR, '..', *path_list)
        paths_to_test = ['.']
        pytest_options = [
            '-s',    # show output from tests; this hides the progress bar though
            '-x',    # stop on first test failure
            '--ff',  # runs last failure first
        ]
        pytest_options += (['-v'] if options.verbose else [])
        os.chdir(location_to_run_in)
        result = pytest.main(paths_to_test + pytest_options)
        if result != 0:
            sys.exit(1)
        failures = False
    else:
        # Codecov seems to work only when using loader.discover. It failed to capture line executions
        # for functions like loader.loadTestFromModule or loader.loadTestFromNames.
        test_suites = unittest.defaultTestLoader.discover(os.path.join(*path_list))
        suite = unittest.TestSuite(test_suites)
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        failures = result.failures
        if result.failures or result.errors:
            sys.exit(1)

    if not failures and options.coverage:
        cov.stop()
        cov.data_suffix = False  # Disable suffix so that filename is .coverage
        cov.save()
        cov.html_report()
        print("HTML report saved in directory 'htmlcov'.")
