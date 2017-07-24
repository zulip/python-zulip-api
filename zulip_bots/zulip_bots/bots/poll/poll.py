# See readme.md for instructions on running this code.

from __future__ import absolute_import
from __future__ import print_function
from six.moves import range

from collections import OrderedDict, namedtuple

def input_from_message_content(message_content):
    lines = message_content.split('\n')
    main_line = lines[0].split(' ')
    command = main_line[0]
    options = main_line[1:]
    title   = ""
    if len(lines) > 1:
        title = lines[1]
    vote_options = []
    if len(lines) > 2:
        vote_options = lines[2:]
    vote_options = [v for v in vote_options if len(v) > 0]
    Input = namedtuple('Input', ['command', 'options', 'title', 'vote_options'])
    return Input(command, options, title, vote_options)

class PollHandler(object):
    def usage(self):
        return '''
            This bot maintains up to one poll per user, per topic, in streams only.
            It currently keeps a running count of the votes, as they are made, with one
            mesage in the stream being updated to show the current status.
            Message the bot privately, appending the stream and topic, or mention it
            within a topic (for new, vote and end commands); if the stream or
            topic contain spaces use a '+' where the space would be.
            '''

    def handle_message(self, message, bot_handler, state_handler):

        help_msg = OrderedDict([
            ('about', "gives a simple summary of this bot."),
            ('help', "produces this help."),
            ('commands', "a concise form of help, listing the supported commands."),
            ('new', ("start a new poll: specify a title on the following line "
                     "and at least two options on subsequent lines.")),
            ('vote', ("vote in an ongoing poll: specify a poll id given in the poll message "
                      "followed by the number of the option to vote for.")),
            ('end', ("end your own ongoing poll.")),
        ])
        stream_topic_notgiven = "\nPlease specify a stream & topic if messaging the bot privately."
        space_equivalent = "+"

        sender = message["sender_email"]
        sender_id = message["sender_id"]

        def private_reply(text):
            bot_handler.send_message(dict(type='private', to=sender, content=text))

        # Break down the text supplied into potential input sets
        inp = input_from_message_content(message['content'])

        # Updates the poll text, based on the current data in the poll (may modify poll)
        # Return True/False, depending if message was successfully posted
        def update_poll_text(poll, stream_topic, force_end=False):
            # Construct initial/updated poll text
            msg = ("Poll by {} (id: {})\n{}\n"
                   .format(poll['creator'], stream_topic[2], poll['title']))
            for i in range(poll['n']):
                msg += ("{}. [{}] {}\n"
                        .format(i+1, len(poll['tallies'][i]), poll[i]))
            if force_end:
                msg += "**This poll has ended**\n"
            # Set/update poll text
            if poll['msg_id'] is None:
                result = bot_handler.send_message(dict(type='stream',
                                                       to=stream_topic[0],
                                                       subject=stream_topic[1],
                                                       content=msg))
                if result['result'] == 'success':
                    poll['msg_id'] = result['id']
                    return (msg, True)
                else:
                    return (msg, False)
            else:
                result = bot_handler.update_message(dict(message_id = poll['msg_id'],
                                                         content = msg))
                if result['result'] == 'success':
                    return (msg, True)
                else:
                    return (msg, False)  # FIXME Cannot always update a message; should poll end?
                    # FIXME Should add handling of return value

        # Quickly return for simple help response cases
        if inp.command == "" or inp.command == "help":
            txt = ("{}\n\nIt supports the following commands:\n"
                   .format(" ".join(self.usage().split())))
            for k, v in help_msg.items():
                txt += "\n**{}** : {}".format(k, v)
            private_reply(txt)
            return
        elif inp.command == "about":
            private_reply(" ".join(self.usage().split()))
            return
        elif inp.command == "commands":
            private_reply("Commands: " + ", ".join((k for k in help_msg)))
            return

        src_is_private = (message['type'] == 'private')

        # Ensure we have some state
        active_polls = state_handler.get_state()
        if active_polls is None:
            active_polls = {}

        if inp.command == "new":
            # Check where the poll will be -> obtain stream_topic
            stream_topic = None
            if src_is_private:
                if len(inp.options) != 2:
                    private_reply(stream_topic_notgiven)
                    return
                else:
                    stream = inp.options[0].replace(space_equivalent, " ")
                    topic = inp.options[1].replace(space_equivalent, " ")
                    stream_topic = (stream, topic, sender_id)
            else:
                stream_topic = (message['display_recipient'], message['subject'], sender_id)
            # Check if a poll is already active with this id
            if stream_topic in active_polls:
                private_reply("Already have a poll with this id; end it explicitly first")
                return
            # Check we have at least a poll title and 2(+) options
            if inp.title == "" or len(inp.vote_options) < 2:
                private_reply("To " + help_msg['new'])
                return
            # Create new poll data
            new_poll = {
                'title': inp.title,  # Poll title
                'tallies': [],   # List of list of sender_id's who voted
                'msg_id': None,  # Message id containing poll text
                'n': len(inp.vote_options),  # How many voting options
                'creator': message['sender_full_name']  # Name of poll creator
            }
            for i, v in enumerate(inp.vote_options):      # Set text & tallies for each vote_option
                new_poll[i] = v
                new_poll['tallies'].append([])
            # Try to send initial poll message to stream/topic, and alert user of result
            (update_msg, success) = update_poll_text(new_poll, stream_topic)
            if success:
                # Insert the new poll and update the state
                active_polls[stream_topic] = new_poll
                state_handler.set_state(active_polls)
                # Generate private message to creator, to indicate successful creation
                msg = ("Poll created in stream '#{}' with topic '{}':\n{}"
                       .format(stream_topic[0], stream_topic[1], update_msg))
            else:
                msg = ("Could not create poll in stream '#{}' with topic '{}'"
                       .format(stream_topic[0], stream_topic[1]))
            private_reply(msg)
        elif inp.command == "vote":
            # Translate options into requested poll and vote
            requested_poll_id = 0
            requested_vote_option = ""
            stream_topic = None
            if src_is_private:
                if len(inp.options) != 4:
                    private_reply("To " + help_msg['vote'] + stream_topic_notgiven)
                    return
                else:
                    requested_poll_id = inp.options[2]
                    requested_vote_option = inp.options[3]
                    stream = inp.options[0].replace(space_equivalent, " ")
                    topic = inp.options[1].replace(space_equivalent, " ")
                    stream_topic = (stream, topic, requested_poll_id)
            else:
                if len(inp.options) != 2:
                    private_reply("To " + help_msg['vote'])
                    return
                else:
                    requested_poll_id = inp.options[0]
                    requested_vote_option = inp.options[1]
                    stream_topic = (message['display_recipient'],
                                    message['subject'], requested_poll_id)
            # Validate requested_poll_id before setting stream_topic & poll
            try:
                requested_poll_id = int(requested_poll_id)
            except ValueError:
                private_reply("To " + help_msg['vote'])
                return
            stream_topic = (stream_topic[0], stream_topic[1], requested_poll_id)
            if stream_topic not in active_polls:
                private_reply("To " + help_msg['vote'])
                return
            poll = active_polls[stream_topic]
            # Check if this user has voted for any option already
            context_txt = (" in the poll on stream '#{}' (topic '{}') titled: '{}'"
                           .format(stream_topic[0], stream_topic[1], poll['title']))
            for i, tally in enumerate(poll['tallies']):
                if sender_id in tally:
                    msg = ("You have already voted{}\n(You voted for {}: {})"
                           .format(context_txt, i+1, poll[i]))
                    private_reply(msg)
                    return
            # Check that vote index is within expected bounds
            vote_index = 0
            try:
                vote_index = int(requested_vote_option)
            except ValueError:
                private_reply("Please select one number to vote for{}".format(context_txt))
                return
            max_vote_index = poll['n']
            if 0 < vote_index <= max_vote_index:  # Indexed from 1
                # Use the vote
                poll['tallies'][vote_index-1].append(sender_id)
                (update_msg, success) = update_poll_text(poll, stream_topic)
                if success:
                    state_handler.set_state(active_polls)
                    msg = ("You just voted{}\n(You voted for {}: {})"
                           .format(context_txt, vote_index, poll[vote_index-1]))
                    private_reply(msg)
                else:
                    private_reply("Could not update the poll with your vote.")
                    # FIXME Should we end the poll automatically here?
            else:
                private_reply(("Please select a number to vote for, between 1-{},{}"
                               .format(max_vote_index, context_txt)))
            return
        elif inp.command == "end":
            # Translate options into stream & topic
            stream_topic = None
            if src_is_private:
                if len(inp.options) != 2:
                    private_reply(stream_topic_notgiven)
                    return
                else:
                    stream = inp.options[0].replace(space_equivalent, " ")
                    topic = inp.options[1].replace(space_equivalent, " ")
                    stream_topic = (stream, topic, sender_id)
            else:
                stream_topic = (message['display_recipient'], message['subject'], sender_id)
            # End the poll if present
            if stream_topic in active_polls:
                (update_msg, success) = update_poll_text(active_polls[stream_topic],
                                                         stream_topic, force_end=True)
                private_reply((("Ending your poll in '#{}' and topic '{}', "
                                "final results were:\n\n{}")
                               .format(stream, topic, update_msg)))
                if not success:
                    private_reply("NOTE: Your poll ended, but the poll message could not be updated.")
                del active_polls[stream_topic]
                state_handler.set_state(active_polls)
            else:
                private_reply(("You do not have a poll in '#{}' and topic '{}'"
                               .format(stream_topic[0], stream_topic[1])))
        else:
            msg = "Unsupported command."
            private_reply(msg)


handler_class = PollHandler
