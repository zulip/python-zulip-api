from zulip_bots.test_lib import BotTestCase

from zulip_bots.bots.converter import utils

class TestConverterBot(BotTestCase):
    bot_name = "converter"

    def test_bot(self) -> None:
        dialog = [
            ("", 'Too few arguments given. Enter `@convert help` '
                 'for help on using the converter.\n'),
            ("foo bar", 'Too few arguments given. Enter `@convert help` '
                        'for help on using the converter.\n'),
            ("2 m cm", "2 m = 200.0 cm\n"),
            ("12.0 celsius fahrenheit", "12.0 celsius = 53.600054 fahrenheit\n"),
            ("0.002 kilometer millimile", "0.002 kilometer = 1.2427424 millimile\n"),
            ("3 megabyte kilobit", "3 megabyte = 24576.0 kilobit\n"),
            ("foo m cm", "`foo` is not a valid number. " + utils.QUICK_HELP + "\n"),
            ("@convert help", "1. conversion: Too few arguments given. "
                              "Enter `@convert help` for help on using the converter.\n"
                              "2. conversion: " + utils.HELP_MESSAGE + "\n"),
            ("2 celsius kilometer", "`Meter` and `Celsius` are not from the same category. "
                                    "Enter `@convert help` for help on using the converter.\n"),
            ("2 foo kilometer", "`foo` is not a valid unit."
                                " Enter `@convert help` for help on using the converter.\n"),
            ("2 kilometer foo", "`foo` is not a valid unit."
                                "Enter `@convert help` for help on using the converter.\n"),


        ]
        self.verify_dialog(dialog)
