import zulip
from threading import Thread

welcome_text = '''
Hello {}, Welcome to Zulip!
* The first thing you should do is to install the development environment. We recommend following the vagrant setup as it is well documented and used by most of the contributors. If you face any trouble during installation post it in #development help
* If you have not used Zulip before play with Zulip for a while. See how is Zulip diffrent from other chat applications. We would love to hear your first impressions about Zulip. Post it in #feedback . We have mobile apps as well as desktop apps too. You should try them too if you have time :)
* Once you are familarized with Zulip a bit you can start contributing. Some of the main projects you can contribute to are Zulip [server](https://github.com/zulip/zulip), [mobile app](https://github.com/zulip/zulip-mobile), [desktop](https://github.com/zulip/zulip-electron) app etc. We even have even a [bot](https://github.com/zulip/zulipbot) that you can contribute to!!
* We host our source code on GitHub. If you are not familiar with Git or GitHub checkout [this](http://zulip.readthedocs.io/en/latest/git-guide.html) guide. You don't have to learn everything but please go through it and learn the basics. We are here to help you if you are having any trouble. Post your questions in #git help .
* Once you have completed these steps you can start contributing. You should start with issues labelled [bite-size](https://github.com/zulip/zulip/issues?q=is%3Aissue+is%3Aopen+label%3A). Bite-size issues are meant for new contributors and can be solved easily as compared to other issues. Currently we have bite-size labels only in Zulip server but if you want a bite size issue for mobile or electron feel free post in #mobile or #electron .
* Solving the first issue can be difficult. The key is not give up. If you spend enough time on the issue you would be able to solve it no matter what.
* Use grep command when you can't figure out what files to change :) For example if you want know what files to modify in order to change Invite more users to Add more users which you can see below the user status list, grep for "Invite more users" in terminal.
* If you are stuck at something and can't figure out what to do you can ask for help in #development help . But make sure that you tried your best to figure out the issue by yourself.
* If you are here for #Outreachy 2017-2018 or #GSoC don't worry much about whether you will get selected or not. You will learn a lot contributing to Zulip in course of next few months and if you do a good job at that you will get selected too :)
* Most important of all welcome to the Zulip family :octopus:

If you have any questions, send me a message, and I will try to respond!
'''

class WelcomeHandler():
    def handle_event(self, event):
        if event['type'] != 'realm_user' or event['op'] != 'add':
            return
        self.client.send_message({
            'type': 'private',
            'to': event['person']['email'],
            'content': welcome_text.format(event['person']['full_name'])
        })
    
    def start_event_handler(self):
        print("Starting event handler...")
        self.client.call_on_each_event(self.handle_event, event_types=["realm_user"])
    
    def __init__(self, client):
        self.client = client
        thread = Thread(target=self.start_event_handler)
        thread.daemon = True
        thread.start()
