"""Used to mainly compose a decorated report for the user
"""

from typing import Dict, Text, List


def compose(results: Dict) -> Text:
    """Composes a report based on test results

    An example would be:

    Status: tests_failed
    Enabled checkers: seo
    Failures from checkers: seo (3)
    More info: https://monkeytest.it/...

    This function assumes that the result dict is valid and does not contain
    any "errors" like bad url

    :param results: A dictionary containing the results of a check
    :return: A response string containing the full report
    """
    if "error" in results:
        return "Error: {}".format(results['error'])

    response = ""

    response += "{}\n".format(print_status(results))

    if "success" in response.lower():
        response += "{}".format(print_test_id(results))
        return response

    response += "{}\n".format(print_enabled_checkers(results))
    response += "{}\n".format(print_failures_checkers(results))
    response += "{}".format(print_more_info_url(results))

    return response


def print_more_info_url(results: Dict) -> Text:
    """Creates info for the test URL from monkeytest.it

    Example:

    More info: https://monkeytest.it/test/...

    :param results: A dictionary containing the results of a check
    :return: A response string containing the url info
    """
    return "More info: {}".format(results['results_url'])


def print_test_id(results: Dict) -> Text:
    """Prints the test-id with attached to the url

    :param results: A dictionary containing the results of a check
    :return: A response string containing the test id
    """
    return "Test: https://monkeytest.it/test/{}".format(results['test_id'])


def print_failures_checkers(results: Dict) -> Text:
    """Creates info for failures in enabled checkers

    Example:

    Failures from checkers: broken_links (3), seo (5)

    This means that the check has 8 section failures, 3 sections in
    broken_links and the other 5 are in seo.

    :param results: A dictionary containing the results of a check
    :return: A response string containing number of failures in each enabled
             checkers
    """
    failures_checkers = [(checker, len(results['failures'][checker]))
                         for checker in get_enabled_checkers(results)
                         if checker in results['failures']]  # [('seo', 3), ..]

    failures_checkers_messages = ["{} ({})".format(fail_checker[0],
                                  fail_checker[1]) for fail_checker in
                                  failures_checkers]

    failures_checkers_message = ", ".join(failures_checkers_messages)
    return "Failures from checkers: {}".format(failures_checkers_message)


def get_enabled_checkers(results: Dict) -> List:
    """Gets enabled checkers

    For example, if enabled_checkers: {'seo' : True, 'broken_links' : False,
    'page_weight' : true}, it will return ['seo'. 'page_weight']

    :param results: A dictionary containing the results of a check
    :return: A list containing enabled checkers
    """
    checkers = results['enabled_checkers']
    enabled_checkers = []
    for checker in checkers.keys():
        if checkers[checker]:  # == True/False
            enabled_checkers.append(checker)
    return enabled_checkers


def print_enabled_checkers(results: Dict) -> Text:
    """Creates info for enabled checkers. This joins the list of enabled
    checkers and format it with the current string response

    For example, if get_enabled_checkers = ['seo', 'page_weight'] then it would
    return "Enabled checkers: seo, page_weight"

    :param results: A dictionary containing the results of a check
    :return: A response string containing enabled checkers
    """
    return "Enabled checkers: {}".format(", "
                                         .join(get_enabled_checkers(results)))


def print_status(results: Dict) -> Text:
    """Creates info for the check status.

    Example: Status: tests_failed

    :param results: A dictionary containing the results of a check
    :return: A response string containing check status
    """
    return "Status: {}".format(results['status'])
