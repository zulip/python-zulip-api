#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Confluence integration for Zulip
#
# Copyright © 2014 Zulip, Inc.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import os
import zulip
import sys
import json
import requests

from six.moves.configparser import ConfigParser, NoSectionError, NoOptionError

CONFIGFILE = os.path.expanduser("~/.zulip_confluencerc")

INSTRUCTIONS = r"""
confluence-bot --config-file=~/.zuliprc --search="@nprnews,quantum physics"
Send Confluence space and page  to a Zulip stream.

To use this script:
0. Use `Confluence rest api ` to  `Confluence `
1. Set up Confluence authentication, as described below
2. Set up a Zulip bot user and download its `.zuliprc` 
   config file to e.g. `~/.zuliprc`
3. Subscribe the bot to the stream that will receive Confluence updates 
   (default stream: confluence)
4. Test the script by running it manually, like this:
5. Configure a crontab entry for this script. A sample crontab entry
that will process spaces and pages every 5 minutes is:
*/5 * * * * /usr/local/share/zulip/integrations/confluence/confluence [options]

== Setting up Confluence authentications ==

Run this on a personal or trusted machine, because your API key is
visible to local users through the command line or config file.

This bot uses OAuth to authenticate with Confluence. Please create a
~/.zulip_confluencerc with the following contents:

[Confluence_api]
username =
consumer_key =
domain_Url =
config_file=


In order to obtain a consumer key & secret, you must register a
new application under your Confluence account:

1 Log in to https://id.atlassian.com.
2 Click API tokens, then Create API token.  
3 Use Copy to clipboard, and paste the token to your script
  or elsewhere:

"""
parser = zulip.add_default_arguments(argparse.ArgumentParser("Fetch space and page from Confluence."))
parser.add_argument('--instructions',
                    action='store_true',
                    help='Show instructions for the confluence bot setup and exit'
                    )
opts = parser.parse_args()
if opts.instructions:
    print(INSTRUCTIONS)
    sys.exit()
if opts.zulip_config_file:
   zuliprc_path = opts.zulip_config_file

try:
    config = ConfigParser()
    config.read(CONFIGFILE)
    username = config.get('Confluence_api', 'username')
    consumer_key = config.get('Confluence_api', 'consumer_key')
    domain_Url = config.get('Confluence_api', 'domain_Url')
    local_file = config.get('Confluence_api', 'local_file')
except:
    parser.error("Please provide a ~/.zulip_confluencerc")

f = open(local_file, "w+")
f.write('0')
f.close()

def confluence_api() -> None:

    params = ('type', 'page'),
    base_url='https://{}/wiki/rest/api/content'.format(domain_Url)
    auth=(username, consumer_key)
    response = requests.get(base_url, params=params, auth=auth)
    res = response.json()
    print(res)
    # length of json data
    length_api = len(res['results'])
    # Fetch value from database models
    f = open(local_file, "r")
    length_confluence_data = int(f.read())
    # compare the lenth of json from database to the new 
    #length of json which is fetch from api
    # if length of fetch json from api  is greater than 
    #save length then we call zulip api
    if (length_api > length_confluence_data):
        test1_json = (res['results'][length_api-1]['_links']['webui'])
        title = res['results'][length_api-1]['title']
        get_spaces_and_pages = spacepage(test1_json)
        format_page_and_string = "New {} is created with title {}".format(get_spaces_and_pages, title)
        client = zulip.Client(config_file = zuliprc_path)
        request = {
            "type": "stream",
            "to": "confluence",
            "subject": "Page",
            "content": format_page_and_string
        }
        result = client.send_message(request)
        f = open(local_file, "w")
        f.write(str(length_api))
    # if user delete pages or space it become update in database
    elif (length_api < length_confluence_data):
        f = open(local_file, "w")
        f.write(str(length_api))
    return (None)
# here we check if there is updation of space or page
def spacepage(get_spaces_and_pages: str) -> str:
    page_space = get_spaces_and_pages.split('/')
    if ('pages' in page_space):
        return ('page\n')
    else:
        return ("space\n")

confluence_api()


