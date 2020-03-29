from zulip_bots.game_handler import BadMoveException
import html
import requests
import random

from typing import Optional, Any, Dict

class NotAvailableException(Exception):
    def __init__(self, message: str) -> None:
        self.message = message

    def __str__(self) -> str:
        return self.message

class TriviaQuizGameModel(object):
    def __init__(self):
        # This could throw an exception. It will be picked up by
        # game_handler and the game will end
        self.current_board = self.get_trivia_quiz()
        self.scores = {}  # type: Dict[int, int]

    def validate_move(self, answer):
        return answer in "ABCD"

    def make_move(self, move, player_number, is_computer=False):
        if player_number not in self.scores:
            self.scores[player_number] = 0
        if not self.validate_move(move):
            raise BadMoveException("Move not valid")
        if move == self.current_board['correct_letter']:
            self.scores[player_number] += 1
        else:
            self.scores[player_number] -= 1
            if self.scores[player_number] < 0:
                self.scores[player_number] = 0
        self.current_board = self.get_trivia_quiz()
        return {
            'correct': move == self.current_board['correct_letter'],
            'correct_letter': self.current_board['correct_letter'],
            'score': self.scores[player_number]
        }

    def determine_game_over(self, players):
        for player_number, score in self.scores.items():
            if score >= 5:
                # Game over
                return players[player_number]
        return

    def get_trivia_quiz(self) -> Dict[str, Any]:
        payload = self.get_trivia_payload()
        quiz = self.get_quiz_from_payload(payload)
        return quiz

    def get_trivia_payload(self) -> Dict[str, Any]:

        url = 'https://opentdb.com/api.php?amount=1&type=multiple'

        try:
            data = requests.get(url)

        except requests.exceptions.RequestException:
            raise NotAvailableException("Uh-Oh! Trivia service is down.")

        if data.status_code != 200:
            raise NotAvailableException("Uh-Oh! Trivia service is down.")

        payload = data.json()
        return payload

    def get_quiz_from_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        result = payload['results'][0]
        question = result['question']
        letters = ['A', 'B', 'C', 'D']
        random.shuffle(letters)
        correct_letter = letters[0]
        answers = dict()
        answers[correct_letter] = result['correct_answer']
        for i in range(3):
            answers[letters[i+1]] = result['incorrect_answers'][i]

        def fix_quotes(s: str) -> Optional[str]:
            # opentdb is nice enough to escape HTML for us, but
            # we are sending this to code that does that already :)
            #
            # Meanwhile Python took until version 3.4 to have a
            # simple html.unescape function.
            try:
                return html.unescape(s)
            except Exception:
                raise Exception('Please use python3.4 or later for this bot.')
        answers = {
            letter: fix_quotes(answer)
            for letter, answer
            in answers.items()
        }
        quiz = dict(
            question=fix_quotes(question),
            answers=answers,
            correct_letter=correct_letter,
        )
        return quiz
