# Zulip Subversion Integration

Get Zulip notifications for your {{ integration_display_name }} commits by
configuring a `post-commit` hook!

{start_tabs}

1.  {!create-an-incoming-webhook.md!}

1.  {!download-python-bindings.md!}

1.  {!install-requirements.md!}

1.  If your {{ integration_display_name }} server and your Zulip server are
    on the same machine, symlink the `post-commit` hook of your
    {{ integration_display_name }} repository in your
    {{ integration_display_name }} server by running:

    `ln -s {{ integration_path }}/post-commit your-repo/hooks/post-commit`

    Otherwise, copy the `post-commit` hook to your
    {{ integration_display_name }} repository's `/hooks` directory.

    The `post-commit` hook is triggered after every commit.

1.  {!change-zulip-config-file.md!}

1.  Copy the config file to the same directory as the `post-commit` hook.

    `cp {{ config_file_path }} your-repo/hooks`

{end_tabs}

{!congrats.md!}

![SVN commit bot message](/static/images/integrations/svn/001.png)

### Configuration options

You can configure the channel and topic where notifications are sent by
updating the `commit_notice_destination` function in
`{{ config_file_path }}`. By default, notifications are sent to the
**#commits** channel with the repository as the topic name.

### Related documentation

- [`post-commit` Repository Hook](https://svnbook.red-beard.com/en/1.7/svn.ref.svn.c.post-commit.html)
