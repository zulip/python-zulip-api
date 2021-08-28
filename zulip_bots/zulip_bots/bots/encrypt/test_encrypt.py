from zulip_bots.test_lib import BotTestCase, DefaultTests


class TestEncryptBot(BotTestCase, DefaultTests):
    bot_name = "encrypt"

    def test_bot(self) -> None:
        dialog = [
            ("", "Encrypted/Decrypted text: "),
            ("Let's Do It", "Encrypted/Decrypted text: Yrg'f Qb Vg"),
            ("me&mom together..!!", "Encrypted/Decrypted text: zr&zbz gbtrgure..!!"),
            ("foo bar", "Encrypted/Decrypted text: sbb one"),
            ("Please encrypt this", "Encrypted/Decrypted text: Cyrnfr rapelcg guvf"),
        ]
        self.verify_dialog(dialog)
