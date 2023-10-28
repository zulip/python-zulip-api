"""Used to parse message and return a dictionary containing a payload
for extract.py
"""

from json.decoder import JSONDecodeError

from zulip_bots.bots.monkeytestit.lib import extract, report


def execute(message: str, apikey: str) -> str:
    """Parses message and returns a dictionary

    :param message: The message
    :param apikey: A MonkeyTestit api key, presumably in the config file
    :return: A response string
    """

    params = message.split(" ")
    command = params[0]

    if "check" in command.lower():
        len_params = len(params)

        if len_params < 2:
            return failed("You **must** provide at least an URL to perform a check.")

        options = {
            "secret": apikey,
            "url": params[1],
            "on_load": "true",
            "on_click": "true",
            "page_weight": "true",
            "seo": "true",
            "broken_links": "true",
            "asset_count": "true",
        }

        # Set the options only if supplied

        if len_params >= 3:
            options["on_load"] = "true" if params[2] == "1" else "false"
        if len_params >= 4:
            options["on_click"] = "true" if params[3] == "1" else "false"
        if len_params >= 5:
            options["page_weight"] = "true" if params[4] == "1" else "false"
        if len_params >= 6:
            options["seo"] = "true" if params[5] == "1" else "false"
        if len_params >= 7:
            options["broken_links"] = "true" if params[6] == "1" else "false"
        if len_params >= 8:
            options["asset_count"] = "true" if params[7] == "1" else "false"

        try:
            fetch_result = extract.fetch(options)
        except JSONDecodeError:
            return failed(
                "Cannot decode a JSON response. "
                "Perhaps faulty link. Link must start "
                "with `http://` or `https://`."
            )

        return report.compose(fetch_result)

        # The disadvantage here is that the user has to supply every params if
        # the user needs to modify the asset_count. There are probably ways
        # to counteract this, but I think this is more fast to run.
    else:
        return "Unknown command. Available commands: `check <website> [params]`"


def failed(message: str) -> str:
    """Simply attaches a failed marker to a message

    :param message: The message
    :return: String
    """
    return "Failed: " + message
