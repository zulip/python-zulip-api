# -*- coding: utf-8 -*-
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


### REQUIRED CONFIGURATION ###

# TRELLO_API_KEY
#
# Visit https://trello.com/1/appkey/generate to generate
# an APPLICATION_KEY (needs to be logged into Trello)
TRELLO_API_KEY = ""

# TRELLO_TOKEN
#
# To generate a Trello read access Token, visit (needs to be logged into Trello)
# https://trello.com/1/authorize?key=<TRELLO_API_KEY>&name=Issue+Manager&expiration=never&response_type=token&scope=read
#
# Take care to replace <TRELLO_API_KEY> with the appropriate value
TRELLO_TOKEN = ""

# ZULIP_WEBHOOK_URL
#
# The webhook URL that Trello will query
ZULIP_WEBHOOK_URL = ""
