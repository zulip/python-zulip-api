from unittest import TestCase

import zulip


class TestHashUtilDecode(TestCase):
    def test_hash_util_decode(self) -> None:
        tests = [
            ("topic", "topic"),
            (".2Edot", ".dot"),
            (".23stream.20name", "#stream name"),
            ("(no.20topic)", "(no topic)"),
            (".3Cstrong.3Ebold.3C.2Fstrong.3E", "<strong>bold</strong>"),
            (".3Asome_emoji.3A", ":some_emoji:"),
        ]
        for encoded_string, decoded_string in tests:
            with self.subTest(encoded_string=encoded_string):
                self.assertEqual(zulip.hash_util_decode(encoded_string), decoded_string)
