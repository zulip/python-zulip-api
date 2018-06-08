from zulip_bots.test_lib import BotTestCase, DefaultTests
from zulip_bots.request_test_lib import mock_request_exception

class TestStackoverflowBot(BotTestCase, DefaultTests):
    bot_name = "stack_overflow"

    def test_bot(self) -> None:

        # Single-word query
        bot_request = 'restful'
        bot_response = ('''For search term:restful
1 : [What exactly is RESTful programming?](https://stackoverflow.com/questions/671118/what-exactly-is-restful-programming)
2 : [RESTful Authentication](https://stackoverflow.com/questions/319530/restful-authentication)
3 : [RESTful URL design for search](https://stackoverflow.com/questions/319530/restful-authentication)
''')
        with self.mock_http_conversation('test_single_word'):
            self.verify_reply(bot_request, bot_response)

        # Multi-word query
        bot_request = 'what is flutter'
        bot_response = ('''For search term:what is flutter
1 : [What is flutter/dart and what are its benefits over other tools?](https://stackoverflow.com/questions/49023008/what-is-flutter-dart-and-what-are-its-benefits-over-other-tools)
''')
        with self.mock_http_conversation('test_multi_word'):
            self.verify_reply(bot_request, bot_response)

        # Number query
        bot_request = '113'
        bot_response = ('''For search term:113
1 : [INSTALL_FAILED_NO_MATCHING_ABIS res-113](https://stackoverflow.com/questions/47117788/install-failed-no-matching-abis-res-113)
2 : [com.sun.tools.xjc.reader.Ring.get(Ring.java:113)](https://stackoverflow.com/questions/12848282/com-sun-tools-xjc-reader-ring-getring-java113)
3 : [no route to host error 113](https://stackoverflow.com/questions/10516222/no-route-to-host-error-113)
''')
        with self.mock_http_conversation('test_number_query'):
            self.verify_reply(bot_request, bot_response)

        # Incorrect word
        bot_request = 'narendra'
        bot_response = "I am sorry. The search term you provided is not found :slightly_frowning_face:"
        with self.mock_http_conversation('test_incorrect_query'):
            self.verify_reply(bot_request, bot_response)

        # 404 status code
        bot_request = 'Zulip'
        bot_response = 'Uh-Oh ! Sorry ,couldn\'t process the request right now.:slightly_frowning_face:\n' \
                       'Please try again later.'

        with self.mock_http_conversation('test_status_code'):
            self.verify_reply(bot_request, bot_response)

        # Request Exception
        bot_request = 'Z'
        with mock_request_exception():
            self.verify_reply(bot_request, bot_response)
