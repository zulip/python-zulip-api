# Zulip Google Calendar integration

Get Zulip notifications for your Google Calendar events!

### Create Zulip bot for Google Calendar notifications

{start_tabs}

1.  {!create-a-generic-bot.md!}

1.  [Download your bot's `zuliprc` file][download-zuliprc], and save it as
    `.zuliprc` in your `~/` directory.

[download-zuliprc]: /api/configuring-python-bindings#download-a-zuliprc-file

1.  Optionally, to configure the bot, add a **`google-calendar`** section to
    the `.zuliprc` file, like below:

    ```
    [google-calendar]
    interval=30
    channel=core-team
    topic=scheduled events
    ```

    See [configuration options](#configuration-options) for the list of
    available options.

{end_tabs}

### Setup Google OAuth Client ID

{start_tabs}

!!! tip ""

    A free Google account is sufficient for this integration; a Google
    service account is not required.

1.  In the Google Cloud console, go to
    **Menu > Google Auth platform > [Branding][branding-menu]**. If you see
    a message that says **Google Auth platform not configured yet**, click
    **Get Started**, and fill the form with the following details.

    - Under **App Information**, set **App name** to a name of your choice.
      Set **User support email** to your email address from the dropdown.
      Click **Next**.
    - Under **Audience**, select **External**, and click **Next**.
    - Under **Contact Information**, enter your email address, and click
      **Next**.
    - Under **Finish**, review the
      **Google API Services User Data Policy** and if you agree, select
      **I agree**. Click **Continue**, and click **Create**.

1.  Go to the **[Clients][clients-menu]** tab. Click **Create Client**.
    Select **Application type > Desktop app**. Set **Name** to a name of
    your choice, such as `Zulip`, and click **Create**. Save the downloaded
    JSON file as `client_secret.json` in your `~/` directory.

1.  Go to the **[Audience][audience-menu]** tab. Under **Test users**, click **+ Add Users**.
    Enter the email address corresponding to your Google Calendar, and click
    **Save**.

[branding-menu]: https://console.cloud.google.com/auth/branding
[clients-menu]: https://console.cloud.google.com/auth/clients
[audience-menu]: https://console.cloud.google.com/auth/audience

{end_tabs}

### Run the integration script

{start_tabs}

1.  Download and
    [install the Zulip Python API](/api/installation-instructions) with:

    `pip install zulip`

1.  Install the requirements for the integration script with:

    `python {{ integration_path }} --provision`

1.  Run the integration script with:

    `python {{ integration_path }}`

    Authorize access in the browser window that opens, to allow the Zulip
    bot to view your Calendar. If you've set `noauth_local_webserver` to
    true, follow the terminal prompts instead, and paste the resulting
    authorization code.

1.  Optionally, pass command-line arguments to reconfigure the integration.
    The command-line arguments override the corresponding settings in the
    `.zuliprc` file.

    `python {{ integration_path }} --interval 30 --channel core-team --topic "scheduled events"`

    See [configuration options](#configuration-options) for the list of
    available options.

1.  You will get notifications as long as the terminal session with the bot
    remains open. Consider using `screen` to run the bot in the background.
    You can restart the integration at any time by re-running the
    integration script.

!!! tip ""

    Newly added calendar events may take up to 10 minutes to generate
    notifications.

{end_tabs}

### Configuration options

The integration can be configured by:

- Passing command-line arguments to the integration script.
- Editing the `google-calendar` section of the `zuliprc` file.

The configuration settings in `zuliprc` will be overridden by the
corresponding command-line options, if both are used.

The integration script accepts the following configuration options:

- `interval`: How many minutes in advance you want reminders delivered.
  The default value is 30 minutes.

- `channel`: The name of the Zulip channel you want to receive
  notifications in. By default, messages are sent as direct messages to the
  bot's owner.

- `topic`: The name of the Zulip topic you want to receive notifications
  in. This option is ignored if the `channel` option is unspecified. If the
  `channel` option is specified, the default topic is "calendar-reminders".

- `client-secret-file`: The path to the file containing the client secret.
  By default, the client secret file is assumed to be at
  `~/client_secret.json`.

- `tokens-file`: The path to the file where the OAuth tokens are stored. By
  default, the tokens file is generated at `~/google-tokens.json` when the
  integration is first run, and is rewritten every hour.

- `noauth-local-webserver`: This option stops the integration script from
  starting a local webserver for receiving OAuth tokens. The default
  authorization process runs a local web server, which requires a browser on
  the same machine. For non-interactive environments and machines without
  browser access, e.g., remote servers, this option allows manual
  authorization. The authorization URL is printed, which the user can copy
  into a browser, copy the resulting authorization code, and paste back into
  the command line.

- `calendar`: The `calendar ID` of the Google calendar to get events from.
  By default, the `primary` calendar is used.

- `format-message`: The template for the message that is sent to Zulip. This
  Python f-string supports Markdown, and can use the following variables:
  `start`, `end`, `title`, `description`, `calendar_link`, `location`,
  `google_meet_link`.

    !!! warn ""

        **Note:** The `title`, `description`, `location`, and
        `google_meet_link` variables are optional for Google Calendar
        events, and hence may be empty. Empty fields are displayed as
        "{No title}", "{No description}", "{No location}", and "{No link}"
        in the message template.

    The default message template takes the following form when all the event
    field variables are non-empty.

    `The event [{title}]({calendar_link}), at {location}, is from {start} to {end}.\n> {description}\n\n[Join call]({google_meet_link}).`

### Related documentation

- [Google's documentation on configuring the OAuth consent screen][consent-screen]
- [Google's documentation on setting up OAuth Client IDs][client-secret]

[consent-screen]: https://developers.google.com/workspace/calendar/api/quickstart/python#configure_the_oauth_consent_screen
[client-secret]: https://developers.google.com/workspace/calendar/api/quickstart/python#authorize_credentials_for_a_desktop_application
