# -*- coding: utf-8 -*-
#
from typing import Dict, Text, Optional

# Name of the stream to send notifications to, default is "commits"
STREAM_NAME = 'commits'

# Change these values to configure authentication for the plugin
ZULIP_USER = "git-bot@example.com"
ZULIP_API_KEY = "0123456789abcdef0123456789abcdef"

# commit_notice_destination() lets you customize where commit notices
# are sent to with the full power of a Python function.
#
# It takes the following arguments:
# * repo   = the name of the git repository
# * branch = the name of the branch that was pushed to
# * commit = the commit id
#
# Returns a dictionary encoding the stream and subject to send the
# notification to (or None to send no notification).
#
# The default code below will send every commit pushed to "master" to
# * stream "commits"
# * topic "master"
# And similarly for branch "test-post-receive" (for use when testing).
def commit_notice_destination(repo, branch, commit):
    # type: (Text, Text, Text) -> Optional[Dict[Text, Text]]
    if branch in ["master", "test-post-receive"]:
        return dict(stream  = STREAM_NAME,
                    subject = u"%s" % (branch,))

    # Return None for cases where you don't want a notice sent
    return None

# Modify this function to change how commits are displayed; the most
# common customization is to include a link to the commit in your
# graphical repository viewer, e.g.
#
# return '!avatar(%s) [%s](https://example.com/commits/%s)\n' % (author, subject, commit_id)
def format_commit_message(author, subject, commit_id):
    # type: (Text, Text, Text) -> Text
    return '!avatar(%s) %s\n' % (author, subject)

## If properly installed, the Zulip API should be in your import
## path, but if not, set a custom path below
ZULIP_API_PATH = None

# Set this to your Zulip server's API URI
ZULIP_SITE = "https://zulip.example.com"
