from typing import Any, Dict
import  re
from datetime import datetime
from crontab import CronTab
import os
import subprocess


# Current plan is to have the user send snoozebot a message
# containing the desired interval for a reminder (like 4 days).
# Then snoozebot sets a cron job. Cron then calls a python script,
# ping.py with parameters for the send_message function in the Rest
# API. This is a POST https: request to POST https://yourZulipDomain.zulipchat.com/api/v1/messages
# I am thinking the datetime module might be useful for calculating the required
# inputs for the chron job.  




#Todos: 
# 1) Figure out what the incoming web hook needs to be to have
#    snoozebot send the reminder.
# 2) figure out how to have snoozebot start the cron job
# 3) I'm thinking I am going to need a function in snoozebot
# to handle the incoming web hook from crontab





class SnoozeBotHandler:


    def usage(self) -> str:
        return '''
        Snoozebot is a reminder tool that will message you at your requested time in the future. Currently, Snoozebot
        accepts the format '# time', as in '2 minutes.' With this format, Snoozebot is using the 'now +# time' syntax
        for the At command. If that means nothing to you, no worries, here is an example of what you would type in a 
        zulip reply: @**snoozebot** 4 days
        What that means is, snoozebot, message/mention me in this thread 4 days from this moment.
        In the future, specific date + time formatting will be implemented, such as: @**snoozebot** 4:13PM on 12/01/2027.
        If you have any questions or feedback, please PM me on Zulip Community Chat. -- MLH 
        '''

    def handle_message(self, message: Dict[str, Any], bot_handler: Any) -> None:
        pattern1 = re.compile(r'(\b\d+\s(minute|hour|day|week|month|year))', re.IGNORECASE)
        # hopefully this pattern object will work for any iteration of "snooze for x days/weeks/months...will have to test.
        #pattern1 = re.compile('\b\d+\s(minute|hour|day|week|month|year)[s]?', re.IGNORECASE)
        pattern2 = re.compile(r'(\b\d{1,2}:\d{2}\s?(AM|PM|am|pm)\s?(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday|tomorrow))', re.IGNORECASE)
        #pattern3 will be specific date + time
        # Changing the match variables to use the group method instead of the findall method to get around the tuple issue
        #match = pattern1.findall(message['content'])
        #match2 = pattern2.findall(message['content'])
        match = re.search(pattern1, message['content'])
        match2 = re.search(pattern2, message['content'])
        stream_id = message['stream_id']
        topic = message['subject']
        user = message['sender_full_name']
        heredoc = f"""END 
                   zulip-send --stream '{stream_id}' --subject '{topic}' --message 'Ping! @**{user}**' --config-file ~/python-zulip-api/zulip_bots/zulip_bots/bots/snoozebot/zuliprc 
                   END"""
        
        # Setting up At command (pipe method)
        # zulip_send_command = zulip-send %(stream name) %(message name) %(message)
        # at_command = " %(zulip_send) | at %(time_input)"
			
        
        #setting up the crontab variables here, but realized that At is the right tool, not crontab
        #cron = CronTab(user='root')
        
        
        # message handling
        if message['content'] == '':
            bot_response = "Please specify the **snooze interval**, such as '4 days'. For help, message me with 'help.'"
            bot_handler.send_reply(message, bot_response)
        elif message['content'] == 'help':
            bot_handler.send_reply(message, self.usage())
        else:
            if pattern1.search(message['content']) != None:
            
                x = match.group(1)
                #y = str(x[0])
                z = "Ok, I'll remind you in " + x
                #print(message['content'])
                #print(pattern1)
                # print(message['stream_id'])
                #print(x[0])
                #print(y)
                #print(match)
                #print(match[0])
                #print(pattern1.search(message[content])
                #y.join(x)
                print(x)
                print(heredoc)
                bot_handler.send_reply(message, z)
                # This is where the At job will be called.
                os.system("at now +%s << %s" %(x, heredoc))                
                # Decided to use At instead of cron. keeping just in case
                # job = cron.new(command='echo hello_word')
                # job.minute.every(5)
                # cron.write() 
                emoji_name = 'alarm clock'
                bot_handler.react(message, emoji_name)
            elif pattern2.search(message['content']) != None:
                # print(pattern2.search(message['content'])
                #print(message['content'])
                l = match2.group(1)
                #m = str(l[0])
                n = "Ok, I'll remind you at " + l
                bot_handler.send_reply(message, n)
                os.system("at %s << %s" %(l, heredoc))  

            else: 
                bot_handler.send_reply(message, "Oops, that won't work. Message me with 'help' for help on how to use me.")
        return 

handler_class = SnoozeBotHandler


