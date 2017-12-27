#!/usr/bin/env python
import os
import json
import hashlib
import sys
import argparse
import shutil
import subprocess
import re

from datetime import datetime
from typing import Any, Dict, List, Tuple
# stubs
ZerverFieldsT = Dict[str, Any]
AddedUsersT = Dict[str, int]
AddedChannelsT = Dict[str, int]

# Transported from https://github.com/zulip/zulip/blob/master/zerver/lib/export.py
def rm_tree(path: str) -> None:
    if os.path.exists(path):
        shutil.rmtree(path)

def users2zerver_userprofile(slack_dir: str, realm_id: int, timestamp: Any,
                             domain_name: str) -> Tuple[List[ZerverFieldsT], AddedUsersT]:
    """
    Returns:
    1. zerver_userprofile, which is a list of user profile
    2. added_users, which is a dictionary to map from slack user id to zulip
       user id
    """
    print('######### IMPORTING USERS STARTED #########\n')
    users = json.load(open(slack_dir + '/users.json'))
    zerver_userprofile = []
    added_users = {}
    user_id_count = 1
    for user in users:
        slack_user_id = user['id']
        profile = user['profile']
        DESKTOP_NOTIFICATION = True

        # email
        if 'email' not in profile:
            email = (hashlib.sha256(user['real_name'].encode()).hexdigest() +
                     "@%s" % (domain_name))
        else:
            email = profile['email']

        # avatar
        # ref: https://chat.zulip.org/help/change-your-avatar
        avatar_source = 'U'
        if 'gravatar.com' in profile['image_32']:
            # use the avatar from gravatar
            avatar_source = 'G'

        # timezone
        _default_timezone = "America/New_York"
        timezone = user.get("tz", _default_timezone)
        if timezone is None or '/' not in timezone:
            timezone = _default_timezone

        if user['deleted'] is False:
            if user['real_name'] == '':
                full_name = user['name']
            else:
                full_name = user['real_name']

        # userprofile's quota is hardcoded as per
        # https://github.com/zulip/zulip/blob/e1498988d9094961e6f9988fb308b3e7310a8e74/zerver/migrations/0059_userprofile_quota.py#L18
        userprofile = dict(
            enable_desktop_notifications=DESKTOP_NOTIFICATION,
            is_staff=user.get('is_admin', False),
            avatar_source=avatar_source,
            is_bot=user.get('is_bot', False),
            avatar_version=1,
            autoscroll_forever=False,
            default_desktop_notifications=True,
            timezone=timezone,
            default_sending_stream=None,
            enable_offline_email_notifications=True,
            user_permissions=[],  # This is Zulip-specific
            is_mirror_dummy=False,
            pointer=-1,
            default_events_register_stream=None,
            is_realm_admin=user.get('is_owner', False),
            # invites_granted=0,  # TODO
            enter_sends=True,
            bot_type=1 if user.get('is_bot', False) else None,
            enable_stream_sounds=False,
            is_api_super_user=False,
            rate_limits="",
            last_login=timestamp,
            tos_version=None,
            default_all_public_streams=False,
            full_name=full_name,
            twenty_four_hour_time=False,
            groups=[],  # This is Zulip-specific
            enable_online_push_notifications=False,
            alert_words="[]",
            bot_owner=None,  # This is Zulip-specific
            short_name=user['name'],
            enable_offline_push_notifications=True,
            left_side_userlist=False,
            enable_stream_desktop_notifications=False,
            enable_digest_emails=True,
            last_pointer_updater="",
            email=email,
            date_joined=timestamp,
            last_reminder=timestamp,
            is_superuser=False,
            tutorial_status="T",
            default_language="en",
            enable_sounds=True,
            pm_content_in_desktop_notifications=True,
            is_active=not user['deleted'],
            onboarding_steps="[]",
            emojiset="google",
            emoji_alt_code=False,
            realm=realm_id,
            quota=1073741824,
            # invites_used=0,  # TODO
            id=user_id_count)

        # TODO map the avatar
        # zerver auto-infer the url from Gravatar instead of from a specified
        # url; zerver.lib.avatar needs to be patched
        # profile['image_32'], Slack has 24, 32, 48, 72, 192, 512 size range

        zerver_userprofile.append(userprofile)
        added_users[slack_user_id] = user_id_count
        user_id_count += 1
        print(u"{} -> {}\nCreated\n".format(user['name'], userprofile['email']))
    print('######### IMPORTING USERS FINISHED #########\n')
    return zerver_userprofile, added_users

def channels2zerver_stream(slack_dir: str, realm_id: int, added_users: AddedUsersT,
                           zerver_userprofile: List[ZerverFieldsT]) -> Tuple[List[ZerverFieldsT],
                                                                             List[ZerverFieldsT],
                                                                             AddedChannelsT,
                                                                             List[ZerverFieldsT],
                                                                             List[ZerverFieldsT]]:
    print('######### IMPORTING CHANNELS STARTED #########\n')
    channels = json.load(open(slack_dir + '/channels.json'))
    added_channels = {}
    zerver_stream = []
    stream_id_count = 1
    zerver_subscription = []
    zerver_recipient = []
    subscription_id_count = 1
    zerver_defaultstream = []

    for channel in channels:
        # slack_channel_id = channel['id']

        # map Slack's topic and purpose content into Zulip's stream description.
        # WARN This mapping is lossy since the topic.creator, topic.last_set,
        # purpose.creator, purpose.last_set fields are not preserved.
        description = "topic: {}\npurpose: {}".format(channel["topic"]["value"],
                                                      channel["purpose"]["value"])

        # construct the stream object and append it to zerver_stream
        stream = dict(
            realm=realm_id,
            name=channel["name"],
            deactivated=channel["is_archived"],
            description=description,
            invite_only=not channel["is_general"],
            date_created=float(channel["created"]),
            id=stream_id_count)

        if channel["name"] == "general":
            defaultstream = dict(
                stream=stream_id_count,
                realm=realm_id,
                id=1)
            zerver_defaultstream.append(defaultstream)

        zerver_stream.append(stream)
        added_channels[stream['name']] = stream_id_count

        # construct the recipient object and append it to zerver_recipient
        # type 1: private
        # type 2: stream
        # type 3: huddle
        recipient = dict(
            type_id=stream_id_count,
            id=stream_id_count,
            type=2)
        zerver_recipient.append(recipient)
        # TOODO add recipients for private message and huddles

        # construct the subscription object and append it to zerver_subscription
        for member in channel['members']:
            sub = dict(
                recipient=stream_id_count,
                notifications=False,
                color="#c2c2c2",
                desktop_notifications=True,
                pin_to_top=False,
                in_home_view=True,
                active=True,
                user_profile=added_users[member],
                id=subscription_id_count)
            # The recipient is a stream for stream-readable message.
            # proof :  https://github.com/zulip/zulip/blob/master/zerver/views/messages.py#L240 &
            # https://github.com/zulip/zulip/blob/master/zerver/views/messages.py#L324
            zerver_subscription.append(sub)
            subscription_id_count += 1
            # TOODO add zerver_subscription which correspond to
            # huddles type recipient
            # For huddles:
            # sub['recipient']=recipient['id'] where recipient['type_id']=added_users[member]

            # TOODO do private message subscriptions between each users have to
            # be generated from scratch?

        stream_id_count += 1
        print(u"{} -> created\n".format(channel['name']))

        # TODO map Slack's pins to Zulip's stars
        # There is the security model that Slack's pins are known to the team owner
        # as evident from where it is stored at (channels)
        # "pins": [
        #         {
        #             "id": "1444755381.000003",
        #             "type": "C",
        #             "user": "U061A5N1G",
        #             "owner": "U061A5N1G",
        #             "created": "1444755463"
        #         }
        #         ],
    recipient_id_count = stream_id_count + 1
    subscription_id_count += 1

    for user in zerver_userprofile:
        zulip_user_id = user['id']

        # this maps the recipients and subscriptions
        # related to private messages

        recipient = dict(
            type_id=zulip_user_id,
            id=recipient_id_count,
            type=1)
        zerver_recipient.append(recipient)

        sub = dict(
            recipient=recipient_id_count,
            notifications=False,
            color="#c2c2c2",
            desktop_notifications=True,
            pin_to_top=False,
            in_home_view=True,
            active=True,
            user_profile=zulip_user_id,
            id=subscription_id_count)

        zerver_subscription.append(sub)
        subscription_id_count += 1
        recipient_id_count += 1

    print('######### IMPORTING STREAMS FINISHED #########\n')
    return zerver_defaultstream, zerver_stream, added_channels, zerver_subscription, zerver_recipient

def channelmessage2zerver_message_one_stream(constants: List[Any], channel: str,
                                             added_users: AddedUsersT, added_channels: AddedChannelsT,
                                             zerver_userprofile: List[ZerverFieldsT], ids: List[int],
                                             zerver_subscription: List[ZerverFieldsT]) -> Tuple[List[ZerverFieldsT],
                                                                                                List[ZerverFieldsT]]:
    slack_dir, REALM_ID = constants
    message_id, usermessage_id = ids
    json_names = os.listdir(slack_dir + '/' + channel)
    users = json.load(open(slack_dir + '/users.json'))
    zerver_message = []
    zerver_usermessage = []

    # Check for user mentions and links in the messages
    def sanitize_text(text: str) -> Tuple[str, str, List[int], bool]:
        tokens = text.split(' ')
        rendered_tokens = tokens
        mentioned_users_id = []
        has_link = False
        for iterator in range(len(tokens)):

            if (re.compile(r"<@.|.>").match(tokens[iterator])):
                tokens[iterator], rendered_tokens[iterator], user_id = check_user_mentions(tokens[iterator])
                mentioned_users_id.append(user_id)

            if ('http://' in tokens[iterator] or 'https://' in tokens[iterator]):
                tokens[iterator], rendered_tokens[iterator] = check_link(tokens[iterator])
                has_link = True

        token = ' '.join(tokens)
        rendered_token = ' '.join(rendered_tokens)
        return token, rendered_token, mentioned_users_id, has_link

    def check_user_mentions(token: str) -> Tuple[str, str, int]:
        token = token.replace('<@', '').replace('>', ' ')
        token = token.replace('|', ' ')
        morphemes = token.split(' ')
        if len(morphemes) > 2:
            short_name = morphemes[1]
        else:
            short_name = ''
        token = morphemes[0]
        for user in users:
            if (user['id'] == token and user['name'] == short_name and len(morphemes) == 3) or \
               (user['id'] == token and len(morphemes) == 2):
                full_name = user['name']
                if ('real_name' in user.keys()):
                    if (user['real_name'] != ''):
                        full_name = user['name']

                user_id = added_users[user['id']]
                token = "@**" + full_name + "** "
                rendered_token = "<span class=\"user-mention\" data-user-email=\"" + user['profile']['email']\
                                 + "\" data-user-id=\"" + str(user_id) + "\">@" + full_name + "</span>"
        return token, rendered_token, user_id

    def check_link(token: str) -> Tuple[str, str]:
        token = token.replace('<', '').replace('>', '')
        rendered_token = "<a href=\"" + token + "\" target=\"_blank\">" + token + "</a>"
        return token, rendered_token

    for json_name in json_names:
        msgs = json.load(open(slack_dir + '/%s/%s' % (channel, json_name)))
        for msg in msgs:
            text = msg['text']
            has_attachment = False
            content, rendered_content, mentioned_users_id, has_link = sanitize_text(text)
            if 'subtype' in msg.keys():
                subtype = msg['subtype']
                if subtype in ["channel_join", "channel_leave", "channel_name"]:
                    continue
            try:
                user = msg.get('user', msg['file']['user'])
            except KeyError:
                user = msg['user']
            # construct message
            zulip_message = dict(
                sending_client=1,
                rendered_content_version=1,  # This is Zulip-specific
                has_image=msg.get('has_image', False),
                subject=channel,  # This is Zulip-specific
                pub_date=float(msg['ts']),
                id=message_id,
                has_attachment=has_attachment,  # attachment will be posted in the subsequent message;
                                                # this is how Slack does it, i.e. less like email
                edit_history=None,
                sender=added_users[user],  # map slack id to zulip id
                content=content,
                rendered_content=rendered_content,  # slack doesn't cache this
                recipient=added_channels[channel],
                last_edit_time=None,
                has_link=has_link)
            zerver_message.append(zulip_message)

            # construct usermessages
            for subscription in zerver_subscription:
                if subscription['recipient'] == zulip_message['recipient']:
                    flags_mask = 1  # For read
                    if subscription['user_profile'] in mentioned_users_id:
                        flags_mask = 9  # For read and mentioned

                    usermessage = dict(
                        user_profile=subscription['user_profile'],
                        id=usermessage_id,
                        flags_mask=flags_mask,
                        message=zulip_message['id'])
                    usermessage_id += 1
                    zerver_usermessage.append(usermessage)
            message_id += 1
    return zerver_message, zerver_usermessage

def main(slack_zip_file: str, realm_name: str) -> None:
    slack_dir = slack_zip_file.replace('.zip', '')
    subprocess.check_call(['unzip', slack_zip_file])
    # with zipfile.ZipFile(slack_zip_file, 'r') as zip_ref:
    #     zip_ref.extractall(slack_dir)

    # TODO fetch realm config from zulip config
    DOMAIN_NAME = "zulipchat.com"

    # Hardcode this to 1, will implement later for zulipchat.com's case where it
    # has multiple realms
    REALM_ID = 1
    NOW = float(datetime.utcnow().timestamp())

    script_path = os.path.dirname(os.path.abspath(__file__)) + '/'
    zerver_realm_skeleton = json.load(open(script_path + 'zerver_realm_skeleton.json'))
    zerver_realm_skeleton[0]['id'] = REALM_ID
    zerver_realm_skeleton[0]['string_id'] = 'zulip'  # subdomain / short_name of realm
    zerver_realm_skeleton[0]['name'] = realm_name
    zerver_realm_skeleton[0]['date_created'] = NOW

    # Make sure the directory output is clean
    output_dir = 'zulip_data'
    rm_tree(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    realm = dict(zerver_client=[{"name": "populate_db", "id": 1},
                                {"name": "website", "id": 2},
                                {"name": "API", "id": 3}],
                 zerver_userpresence=[],  # shows last logged in data, which is not available in slack
                 zerver_userprofile_mirrordummy=[],
                 zerver_realmdomain=[{"realm": REALM_ID,
                                      "allow_subdomains": False,
                                      "domain": DOMAIN_NAME,
                                      "id": REALM_ID}],
                 zerver_useractivity=[],
                 zerver_realm=zerver_realm_skeleton,
                 zerver_huddle=[],
                 zerver_userprofile_crossrealm=[],
                 zerver_useractivityinterval=[],
                 zerver_realmfilter=[],
                 zerver_realmemoji=[])

    zerver_userprofile, added_users = users2zerver_userprofile(slack_dir,
                                                               REALM_ID,
                                                               int(NOW),
                                                               DOMAIN_NAME)
    realm['zerver_userprofile'] = zerver_userprofile

    zerver_defaultstream, zerver_stream, added_channels, zerver_subscription, zerver_recipient = channels2zerver_stream(slack_dir,
                                                                                                                        REALM_ID,
                                                                                                                        added_users,
                                                                                                                        zerver_userprofile)
    # See https://zulipchat.com/help/set-default-streams-for-new-users
    # for documentation on zerver_defaultstream
    realm['zerver_defaultstream'] = zerver_defaultstream
    realm['zerver_stream'] = zerver_stream
    realm['zerver_subscription'] = zerver_subscription
    realm['zerver_recipient'] = zerver_recipient
    # IO realm.json
    realm_file = output_dir + '/realm.json'
    json.dump(realm, open(realm_file, 'w'))

    # now for message.json
    message_json = {}
    zerver_message = []  # type: List[ZerverFieldsT]
    zerver_usermessage = []  # type: List[ZerverFieldsT]
    zerver_attachment = []  # type: List[ZerverFieldsT]

    constants = [slack_dir, REALM_ID]
    for channel in added_channels.keys():
        message_id = len(zerver_message) + 1  # For the id of the messages
        usermessage_id = len(zerver_usermessage) + 1
        ids = [message_id, usermessage_id]
        zm, zum = channelmessage2zerver_message_one_stream(constants, channel,
                                                           added_users, added_channels,
                                                           zerver_userprofile, ids,
                                                           zerver_subscription)
        zerver_message += zm
        zerver_usermessage += zum

    message_json['zerver_message'] = zerver_message
    message_json['zerver_usermessage'] = zerver_usermessage
    # IO message.json
    message_file = output_dir + '/messages-000001.json'
    json.dump(message_json, open(message_file, 'w'))

    # IO avatar records
    avatar_records_file = output_dir + '/avatars/records.json'
    os.makedirs(output_dir + '/avatars', exist_ok=True)
    json.dump([], open(avatar_records_file, 'w'))

    # IO uploads TODO
    uploads_records_file = output_dir + '/uploads/records.json'
    os.makedirs(output_dir + '/uploads', exist_ok=True)
    json.dump([], open(uploads_records_file, 'w'))

    # IO attachments
    attachment_file = output_dir + '/attachment.json'
    attachment = {"zerver_attachment": zerver_attachment}
    json.dump(attachment, open(attachment_file, 'w'))

    # remove slack dir
    rm_tree(slack_dir)

    # compress the folder
    subprocess.check_call(["tar", "-czf", output_dir + '.tar.gz', output_dir])
    # subprocess.check_call(['zip', '-jpr', output_dir + '.zip', realm_file, message_file])

    # remove zulip dir
    rm_tree(output_dir)

    sys.exit(0)

if __name__ == '__main__':
    # from django.conf import settings
    # settings_module = "settings.py"
    # os.environ['DJANGO_SETTINGS_MODULE'] = settings_module
    description = ("Script to convert Slack export data into Zulip export data.")
    parser = argparse.ArgumentParser(description=description)
    if len(sys.argv) != 3:
        sys.stderr.write('Usage: python slackdata2zulipdata.py <slack_zip_file> <realm_name>\n')
        sys.exit(1)
    slack_zip_file, realm_name = sys.argv[1], sys.argv[2]
    main(slack_zip_file, realm_name)
