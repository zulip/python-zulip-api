#!/usr/bin/env python
from zulip_bots.test_lib import StubBotTestCase

class TestLunch(StubBotTestCase):
    bot_name = 'lunch'

    def test_bot(self):
        conversation = [
            # Unknown command
            ('', "I don't think I can do that. :frowning:"),
            # I want (Cheese Cake, Pizza)
            ('I want Cheese Cake, Pizza', "**Here's the new** @**Foo Test User** **list of items:** :wink:\nCheese Cake, Pizza"),
            # user wants (Bread, Pizza)
            ('@user wants Bread, Pizza', "**Here's the new** @**user** **list of items:** :wink:\nBread, Pizza"),
            # copy (adds user's list elements to Foo Test User's list)
            ('@user I want that', "**Here's the new** @**Foo Test User** **list of items:** :wink:\nCheese Cake, Pizza, Bread, Pizza"),
            # remove (Cheese Cake, Bread from the the list)
            ('remove Cheese Cake, Bread', "**Here's the new** @**Foo Test User** **list of items:** :wink:\nPizza, Pizza"),
            # user remove (Pizza from the user's list)
            ('@user remove Pizza', "**Here's the new** @**user** **list of items:** :wink:\nBread"),
            # fail remove (Popcorn isn't on the list)
            ('remove Popcorn', "@**Foo Test User** ** doesn't have Popcorn in the list** :neutral_face:"),
            # user remove all (Deletes user's list)
            ('@user remove all', "Cleared @**user** list! :ok_hand:"),
            # orders (show all orders)
            ('orders', "**Here's the list of orders:**\n Foo Test User **wants** Pizza, Pizza"),
            # order (show my order)
            ('order', "**Here's** @**Foo Test User** **list:**\nPizza, Pizza"),
            # random (pick a random user [Foo Test User will be picked because he is the only one on the list])
            ('who should order lunch?', "**I think @**Foo Test User** should order lunch.** :stuck_out_tongue:"),
            # no user (@fail doesn't exist)
            ('@fail I want that', "Sry, @**fail** isn't hungry. :disappointed:"),
        ]

        self.verify_dialog(conversation)
