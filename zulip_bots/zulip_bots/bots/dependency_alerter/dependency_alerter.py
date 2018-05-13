import requests
import os
from datetime import datetime

from typing import Any, Dict, List, Tuple

# See doc.md for instructions on running this code.

class DependencyAlerterHandler:
    '''
    This Bot reads a specified file for a list of python project dependencies,
    and semi-regularly polls PyPI to check if a newer version exists.
    '''

    META = {
        'name': 'Dependency-alerter',
        'description': 'Alerts when newer versions of specified python packages are available.',
    }

    def usage(self) -> str:
        return ''' '''

    async def handle_message_async(self, message: Dict[str, str], bot_handler: Any) -> None:
        # Specify named repositories/urls where the requirements.txt files exist in 'repos'
        repos = {'x': 'http://foo', 'y': 'http://example.com', 'z': 'http://github.com/zulip/ginger'}
        server_url = 'https://github.com/zulip/zulip/raw/master/requirements/{}.txt'
        for server_req in ('dev', 'docs', 'mypy', 'pip', 'prod', 'thumbor'):
            repos['server-'+server_req] = server_url.format(server_req)

        help_title = ("Mention this bot with one of the following to list the "
                      "current and available dependencies for the following repos/branches:\n")
        help_text = (help_title +
                     "\n".join("**{}**: {}".format(name, repos[name]) for name in sorted(repos)))

        content = message['content'].lower()

        if content == '' or content == 'help':
            bot_handler.send_reply(message, help_text)
            return

        if content not in repos:
            not_found_text = "The named repo, **{}**, is not known.\n\n".format(content) + help_text
            bot_handler.send_reply(message, not_found_text)
            return

        repo = "**{}**".format(content)

        try:
            text = await download_requirements_txt(repos[content])
        except DownloadException as e:
            bot_handler.send_reply(message, str(e).format(repo))
            return

        packages = await minimal_current_package_versions(text)
        package_versions = await collect_current_versions(packages)

        if len(package_versions) == 0:
            bot_handler.send_reply(message, "No packages at URL for {}.".format(repo))
            return

        out_of_date_packages = {package: (curr, avail)
                                for package, (curr, avail) in package_versions.items()
                                if avail and curr != avail}

        if len(out_of_date_packages) == 0:
            bot_handler.send_reply(message, "All packages up to date for {}.".format(repo))
            return

        package_width = max(len(package) for package in out_of_date_packages)
        versions = ["{:{width}} {:>9} / {:9}".format(package, curr, avail, width=package_width)
                    for package, (curr, avail) in out_of_date_packages.items()]
        output = (["The following dependencies appear to not be up to date for {}:".format(repo)] +
                  ["```"] +
                  [" "*package_width + " {:>9} / available".format("current")] +
                  sorted(versions))
        bot_handler.send_reply(message, "\n".join(output))

class DownloadException(Exception):
    pass

async def download_requirements_txt(url: str) -> List[str]:
    connection_failure = None
    response = None
    try:
        response = requests.get(url)
    except requests.exceptions.ConnectionError:
        connection_failure = "Connection error"
    except requests.exceptions.RequestException:
        connection_failure = "General connection error"

    if connection_failure is not None or (response is not None and response.status_code != 200):
        download_failure_text = "Failed to download URL for {}.\n"
        if connection_failure is not None:
            download_failure_text += "{}.".format(connection_failure)
        else:
            download_failure_text += "Location inaccessible on server."
        raise DownloadException(download_failure_text)

    assert response is not None
    return response.iter_lines(decode_unicode=True)

async def minimal_current_package_versions(requirements_txt_lines: List[str]) -> Dict[str, str]:
    package_lines = [line.strip().split("==") for line in requirements_txt_lines
                     if '==' in line and line != '\n' and line[0] != '#' and ' # via ' not in line]
    return dict((line[0], line[1]) for line in package_lines if len(line) == 2)

async def collect_current_versions(packages: Dict[str, str]) -> Dict[str, Tuple[str, str]]:
    # Python 3.6 is required for await/async in list comprehensions, so with 3.5 must use for loop, not:
    # versions = {p: (v, await latest_version_by_date(p, session)) for p, v in packages.items()}
    versions = dict()
    for p, v in packages.items():
        versions[p] = (v, await latest_version_by_date(p))
    return versions

async def latest_version_by_date(package_name: str) -> str:
    data = requests.get("https://pypi.org/pypi/{}/json".format(package_name))
    if data.status_code == 200:
        version_uploads = [(version, [datetime.strptime(upload['upload_time'], "%Y-%m-%dT%H:%M:%S")
                                      for upload in data])
                           for version, data in data.json()['releases'].items()]
        first_version_uploads = {version: min(uploads) if uploads else datetime.min
                                 for version, uploads in version_uploads}
        latest_upload = (datetime.min, "")
        for version, upload in first_version_uploads.items():
            if upload > latest_upload[0]:
                latest_upload = (upload, version)
        return latest_upload[1]
    return ""

# This is not currently used
def available_versions(package_name: str) -> List[str]:
    data = requests.get("https://pypi.org/pypi/{}/json".format(package_name))
    if data.status_code == 200:
        return sorted(data.json()['releases'].keys())
    return []


handler_class = DependencyAlerterHandler
