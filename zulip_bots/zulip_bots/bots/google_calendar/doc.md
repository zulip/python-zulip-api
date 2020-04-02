# Google Calendar bot

This bot facilitates creating Google Calendar events.

## Setup

1. Register a new project in the
   [Google Developers Console](https://console.developers.google.com/start).
2. Enable the Google Calendar API in the Console.
3. Download the project's "client secret" JSON file to a path of your choosing.
4. Go to `<python_zulip_api_root>/zulip/integrations/google/`.
5. Run the Google OAuth setup script, which will help you generate the
   tokens required to operate with your Google Calendar:

    ```bash
    $ python oauth.py \
        --secret_path <your_client_secret_file_path> \
        -s https://www.googleapis.com/auth/calendar
    ```

   The `--secret_path` must match wherever you stored the client secret
   downloaded in step 3.

   You can also use the `--credential_path` argument, which is useful for
   specifying where you want to store the generated tokens. Please note
   that if you set a path different to `~/.google_credentials.json`, you
   have to modify the `CREDENTIAL_PATH` constant in the bot's
   `google_calendar.py` file.
6. Install the required dependencies:

    ```bash
    $ sudo apt install python3-dev
    $ pip install -r requirements.txt
    ```
7. Prepare your `.zuliprc` file and run the bot itself, as described in
   ["Running bots"](https://chat.zulip.org/api/running-bots).

## Usage

For delimited events:

    @gcalendar <event_title> | <start_date> | <end_date> | <timezone> (optional)

For full-day events:

    @gcalendar <event_title> | <start_date>

For detailed help:

    @gcalendar help

Here are some examples:

    @gcalendar Meeting with John | 2017/03/14 13:37 | 2017/03/14 15:00:01 | EDT
    @gcalendar Comida | en 10 minutos | en 2 horas
    @gcalendar Trip to LA | tomorrow


Some additional considerations:

- If an ambiguous date format is used, **the American one will have preference**
  (`03/01/2016` will be read as `MM/DD/YYYY`). In case of doubt,
  [ISO 8601](https://en.wikipedia.org/wiki/ISO_8601) format is recommended
  (`YYYY/MM/DD`).
- If a timezone is specified in both a date and in the optional `timezone`
  field, **the one in the date will have preference**.
- You can use **different languages and locales** for dates, such as
  `Martes 14 de enero de 2003 a las 13:37 CET`. Some (but not all) of them are:
  English, Spanish, Dutch and Russian. A full list can be found
  [here](https://dateparser.readthedocs.io/en/latest/#supported-languages).
- The default timezone is **the server\'s**. However, it can be specified at
  the end of each date, in both numerical (`+01:00`) or abbreviated format
  (`CET`).
