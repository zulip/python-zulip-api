from typing_extensions import override

from zulip_bots.test_lib import BotTestCase, DefaultTests


class TestChessBot(BotTestCase, DefaultTests):
    bot_name = "chessbot"

    START_RESPONSE = """New game! The board looks like this:

```
  a b c d e f g h
8 ♜ ♞ ♝ ♛ ♚ ♝ ♞ ♜ 8
7 ♟ ♟ ♟ ♟ ♟ ♟ ♟ ♟ 7
6 · · · · · · · · 6
5 · · · · · · · · 5
4 · · · · · · · · 4
3 · · · · · · · · 3
2 ♙ ♙ ♙ ♙ ♙ ♙ ♙ ♙ 2
1 ♖ ♘ ♗ ♕ ♔ ♗ ♘ ♖ 1
  a b c d e f g h
```


Now it's **white**'s turn.


To make your next move, respond to Chess Bot with

```do <your move>```

*Remember to @-mention Chess Bot at the beginning of your response.*"""

    DO_E4_RESPONSE = """The board was like this:

```
  h g f e d c b a
1 ♖ ♘ ♗ ♔ ♕ ♗ ♘ ♖ 1
2 ♙ ♙ ♙ ♙ ♙ ♙ ♙ ♙ 2
3 · · · · · · · · 3
4 · · · · · · · · 4
5 · · · · · · · · 5
6 · · · · · · · · 6
7 ♟ ♟ ♟ ♟ ♟ ♟ ♟ ♟ 7
8 ♜ ♞ ♝ ♚ ♛ ♝ ♞ ♜ 8
  h g f e d c b a
```


Then *white* moved *e4*:

```
  h g f e d c b a
1 ♖ ♘ ♗ ♔ ♕ ♗ ♘ ♖ 1
2 ♙ ♙ ♙ · ♙ ♙ ♙ ♙ 2
3 · · · · · · · · 3
4 · · · ♙ · · · · 4
5 · · · · · · · · 5
6 · · · · · · · · 6
7 ♟ ♟ ♟ ♟ ♟ ♟ ♟ ♟ 7
8 ♜ ♞ ♝ ♚ ♛ ♝ ♞ ♜ 8
  h g f e d c b a
```


Now it's **black**'s turn.


To make your next move, respond to Chess Bot with

```do <your move>```

*Remember to @-mention Chess Bot at the beginning of your response.*"""

    DO_KE4_RESPONSE = """Sorry, the move *Ke4* isn't legal.

```
  h g f e d c b a
1 ♖ ♘ ♗ ♔ ♕ ♗ ♘ ♖ 1
2 ♙ ♙ ♙ · ♙ ♙ ♙ ♙ 2
3 · · · · · · · · 3
4 · · · ♙ · · · · 4
5 · · · · · · · · 5
6 · · · · · · · · 6
7 ♟ ♟ ♟ ♟ ♟ ♟ ♟ ♟ 7
8 ♜ ♞ ♝ ♚ ♛ ♝ ♞ ♜ 8
  h g f e d c b a
```


To make your next move, respond to Chess Bot with

```do <your move>```

*Remember to @-mention Chess Bot at the beginning of your response.*"""

    RESIGN_RESPONSE = """*Black* resigned. **White** wins!

```
  h g f e d c b a
1 ♖ ♘ ♗ ♔ ♕ ♗ ♘ ♖ 1
2 ♙ ♙ ♙ · ♙ ♙ ♙ ♙ 2
3 · · · · · · · · 3
4 · · · ♙ · · · · 4
5 · · · · · · · · 5
6 · · · · · · · · 6
7 ♟ ♟ ♟ ♟ ♟ ♟ ♟ ♟ 7
8 ♜ ♞ ♝ ♚ ♛ ♝ ♞ ♜ 8
  h g f e d c b a
```"""

    @override
    def test_bot_responds_to_empty_message(self) -> None:
        with self.mock_config_info({"stockfish_location": "/foo/bar"}):
            response = self.get_response(dict(content=""))
            self.assertIn("play chess", response["content"])

    def test_main(self) -> None:
        with self.mock_config_info({"stockfish_location": "/foo/bar"}):
            self.verify_dialog(
                [
                    ("start with other user", self.START_RESPONSE),
                    ("do e4", self.DO_E4_RESPONSE),
                    ("do Ke4", self.DO_KE4_RESPONSE),
                    ("resign", self.RESIGN_RESPONSE),
                ]
            )
