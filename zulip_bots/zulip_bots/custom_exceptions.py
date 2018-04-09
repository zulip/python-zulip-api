# This file implements some custom exceptions that can
# be used by all bots.
# We avoid adding these exceptions to lib.py, because the
# current architecture works by lib.py importing bots, not
# the other way around.

class ConfigValidationError(Exception):
    '''
    Raise if the config data passed to a bot's validate_config()
    is invalid (e.g. wrong API key, invalid email, etc.).
    '''

class FileUploadError(Exception):
    '''
    Raise if the file upload to a Zulip server fails.
    '''
    def __init__(self, msg, payload):
        super(FileUploadError, self).__init__(msg)
        self.payload = payload  # the complete dict from the upload_file method.
