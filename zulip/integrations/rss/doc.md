# Zulip RSS Integration

Get updates from RSS feeds in Zulip!

!!! tip ""

    [The Zapier integration][1] is usually a simpler way to
    integrate RSS with Zulip.

[1]: ./zapier

{start_tabs}

1.  {!create-an-incoming-webhook.md!}

    Download the `zuliprc` configuration file of your bot by clicking the
    download (<i class="fa fa-download"></i>) icon under the bot's name, and
    save to `~/.zuliprc`.

1.  {!download-python-bindings.md!}

1.  {!install-requirements.md!}

1.  Create a file containing RSS feed URLs, with one URL per line, at
    `~/.cache/zulip-rss/rss-feeds`. To use a different location, pass the
    `--feed-file` [option](#configuration-options) to the integration
    script.

1.  Run the bot to send summaries of RSS entries from your favorite feeds,
    with the command:

    `{{ integration_path }}/rss-bot`

1.  Optionally, pass command-line arguments to re-configure the integration.
    See [the configuration options](#configuration-options) below.

    ```
    {{ integration_path }}/rss-bot \
    --feed-file="home/user/zulip-rss/rss-feeds" \
    --data-dir="home/user/zulip-rss" \
    --stream="news" \
    --topic="rss" \
    --unwrap --math
    ```

1.  Configure a crontab entry to keep the integration running.

    This sample crontab entry processes feeds stored in the default
    location and posts to the "rss" topic in the **#news** channel every 5
    minutes:

    `*/5 * * * * {{ integration_path }}/rss-bot --stream="news" --topic="rss"`

{end_tabs}

{!congrats.md!}

![RSS bot message](/static/images/integrations/rss/001.png)

### Configuration options

The integration script accepts the following command-line arguments.

- `--feed-file`: The path to the file containing the RSS feed URLs. The
  default location is `~/.cache/zulip-rss/rss-feeds`.

- `--data-dir`: The directory where feed metadata is stored. The default
  location is `~/.cache/zulip-rss`.

- `--stream`: The name of the Zulip channel you want to receive
  notifications in. By default, messages are sent to the **#rss** channel.

- `--topic`: The name of the topic to which the RSS entries will be posted.
  By default, for each RSS feed URL specified, the feed's title is used for
  the topic name.

- `--unwrap`: This option converts word-wrapped paragraphs in the message
  content into single lines.

- `--math`: This option converts `$` in the message content to `$$`, for
  KaTeX processing.
