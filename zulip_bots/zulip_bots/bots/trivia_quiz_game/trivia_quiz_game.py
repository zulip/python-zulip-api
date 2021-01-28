from typing import Optional, Any, Dict, Tuple, Union
import json

from zulip_bots.game_handler import GameAdapter
from zulip_bots.bots.trivia_quiz_game.controller import TriviaQuizGameModel

class TriviaQuizGameMessageHandler(object):
    def parse_board(self, question: Dict[str, Any]) -> Union[Tuple[str, str], str]:
        bot_response = self.format_quiz_for_markdown(question)
        widget_content = self.format_quiz_for_widget(question)
        return bot_response, widget_content

    def format_quiz_for_widget(self, question: Dict[str, Any]) -> str:
        widget_type = 'zform'
        question_str = question['question']
        answers = question['answers']

        heading = question_str

        def get_choice(letter: str) -> Dict[str, str]:
            answer = answers[letter]
            reply = letter

            return dict(
                type='multiple_choice',
                short_name=letter,
                long_name=answer,
                reply=reply,
            )

        choices = [get_choice(letter) for letter in 'ABCD']

        extra_data = dict(
            type='choices',
            heading=heading,
            choices=choices,
        )

        widget_content = dict(
            widget_type=widget_type,
            extra_data=extra_data,
        )
        payload = json.dumps(widget_content)
        return payload

    def format_quiz_for_markdown(self, question: Dict[str, Any]) -> str:
        question_str = question['question']
        answers = question['answers']
        answer_list = '\n'.join([
            '* **{letter}** {answer}'.format(
                letter=letter,
                answer=answers[letter],
            )
            for letter in 'ABCD'
        ])
        how_to_respond = '''**reply**: <letter>'''

        content = '''
Q: {question}

{answer_list}
{how_to_respond}'''.format(
            question=question_str,
            answer_list=answer_list,
            how_to_respond=how_to_respond,
        )
        return content

    def get_player_color(self, turn: int) -> Optional[str]:
        # There is no player colour, players don't play with tokens
        return None

    def alert_move_message(self, original_player: str, move_info: str, move_data: Any = None) -> str:
        if move_data['correct']:
            return ":tada: Correct {} ({} points)!".format(original_player, move_data['score'])
        return ":disappointed: Incorrect {} ({} points). The correct answer was **{}**".format(
            original_player, move_data['score'], move_data['correct_letter'])

    def game_start_message(self) -> str:
        return 'Answer the questions correctly, and try to get the most points!\n Good luck!'

class TriviaQuizGameBotHandler(GameAdapter):
    '''
    Bot that uses the Game Adapter class
    to allow users to play other users
    or the computer in a Trivia Game
    '''
    def __init__(self) -> None:
        game_name = 'Trivia'
        bot_name = 'trivia_quiz'
        move_help_message = '* To answer a question, click an answer button'
        move_regex = '([ABCD])'
        model = TriviaQuizGameModel
        gameMessageHandler = TriviaQuizGameMessageHandler
        rules = 'Get the most points in the quiz!'
        super(TriviaQuizGameBotHandler, self).__init__(
            game_name,
            bot_name,
            move_help_message,
            move_regex,
            model,
            gameMessageHandler,
            rules,
            max_players=4,
            min_players=1,
            supports_computer=False
        )

handler_class = TriviaQuizGameBotHandler
