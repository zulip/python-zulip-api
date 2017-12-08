import random

ORDERS = {}

class LunchBotHandler(object):

    def usage(self):
        return '''
        This is a small Zulip bot for organizing lunch with your friends and
        coworkers.
        '''

    def handle_message(self, message, bot_handler):
        content = self.keyword_selection(message)
        bot_handler.send_reply(message, content)

    def keyword_selection(self, message):
        msg = message['content'].split()

        if len(msg) == 0:
            return "I don't think I can do that. :frowning:"

        user = message['sender_full_name']
        if msg[0][0] == '@':
            user = msg[0][1:].replace('**', '')
            msg  = msg[1:]

        if len(msg) == 0:
            return

        if msg[-1] == 'that':
            return copy_user_list(user, message['sender_full_name'])

        if msg[0:2] == ['I', 'want']:
            return add_to_user_list(user, msg[2:])

        if msg[0] == 'wants':
            return add_to_user_list(user, msg[1:])

        if msg == ['remove', 'all']:
            return remove_all(user)

        if msg[0] == 'remove':
            return remove_from_user_list(user, msg[1:])

        if msg[0] == 'orders':
            return show_all_orders()

        if msg[0] == 'order':
            return show_order(user)

        if msg[0:2] == ['who', 'should']:
            return random_user(msg[2:])

        if msg[0] == 'help':
            return '''
                <user|optional> (I) want(s) <item>
                Adds <item> to the sender's (or <user>'s if specified) list of items

                <user> I want that
                Adds every item in <user>'s list of items to the sender's list of items

                <user|optional> remove <item>
                Removes <item> to the sender's (or <user>'s if specified) list of items

                <user|optional> remove all
                Removes all items to the sender's (or <user>'s if specified) list of items

                orders
                Show all orders

                <user|optional> order
                Shows all items of the sender's (or <user>'s if specified) list of items

                who should <verb>(?)
                Randomly selects a user from the orders list

                help
                Shows help (this section)
            '''

        return "I don't think I can do that. :frowning:"

def find_user(user, error):
    try:
        ORDERS[user]
    except KeyError:
        if error:
            return (True, 'Sry, @**' + user + "** isn't hungry. :disappointed:")
        else:
            ORDERS[user] = []
            return (True, 'User created!')
    else:
        return (False, 'User exists!')

def item_interpreter(items):
    item_str = ''
    for item in items:
        if len(item_str) == 0:
            item_str += ' ' + item
        else:
            if item_str[-1] == ',':
                item_str += item
            else:
                item_str += ' ' + item

    return item_str[1:].split(',')

def copy_user_list(original_user, user):
    user_not_found = find_user(original_user, True)
    if user_not_found[0]:
        return user_not_found[1]
    find_user(user, False)

    ORDERS[user].extend(ORDERS[original_user])

    return "**Here's the new** @**" + user + '** **list of items:** :wink:\n' + ', '.join(ORDERS[user])

def add_to_user_list(user, items):
    find_user(user, False)

    items = item_interpreter(items)
    ORDERS[user].extend(items)

    return "**Here's the new** @**" + user + '** **list of items:** :wink:\n' + ', '.join(ORDERS[user])

def remove_from_user_list(user, items):
    user_not_found = find_user(user, True)
    if user_not_found[0]:
        return user_not_found[1]

    items = ' '.join(items)
    if ',' in items:
        items = items.split(', ')
        for item in items:
            try:
                ORDERS[user].remove(item)
            except ValueError:
                return "@**" + user + "** ** doesn't have " + item + " in the list** :neutral_face:"
    else:
        try:
            ORDERS[user].remove(items)
        except ValueError:
            return "@**" + user + "** ** doesn't have " + items + " in the list** :neutral_face:"

    return "**Here's the new** @**" + user + '** **list of items:** :wink:\n' + ', '.join(ORDERS[user])

def remove_all(user):
    user_not_found = find_user(user, True)
    if user_not_found[0]:
        return user_not_found[1]

    del ORDERS[user]

    return 'Cleared @**' + user + '** list! :ok_hand:'

def show_all_orders():
    order_str = ''
    for order in ORDERS:
        order_str = order + ' **wants** ' + ', '.join(ORDERS[order])

    return "**Here's the list of orders:**\n " + order_str

def show_order(user):
    user_not_found = find_user(user, True)
    if user_not_found[0]:
        return user_not_found[1]

    return "**Here's** @**" + user + '** **list:**\n' + ', '.join(ORDERS[user])

def random_user(verb):
    users = list(ORDERS.keys())

    verb = ''.join(item_interpreter(verb))
    if verb[-1] == '?':
        verb = verb[:-1]

    if len(users) == 0:
        return "**No one wants to " + verb + "**. :anguished:"

    user = random.choice(users)

    return "**I think @**" + user + "** should " + verb + ".** :stuck_out_tongue:"

handler_class = LunchBotHandler
