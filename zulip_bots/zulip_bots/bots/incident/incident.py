import json
import re
from typing import Any, Dict, Tuple

from zulip_bots.lib import BotHandler

QUESTION = "How should we handle this?"

ANSWERS = {
    "1": "known issue",
    "2": "ignore",
    "3": "in process",
    "4": "escalate",
}


class InvalidAnswerError(Exception):
    pass


class IncidentHandler:
    def usage(self) -> str:
        return """
            This plugin lets folks reports incidents and
            triage them.  It is intended to be sample code.
            In the real world you'd modify this code to talk
            to some kind of issue tracking system.  But the
            glue code here should be pretty portable.
            """

    def handle_message(self, message: Dict[str, Any], bot_handler: BotHandler) -> None:
        query = message["content"]
        if query.startswith("new "):
            start_new_incident(query, message, bot_handler)
        elif query.startswith("answer "):
            try:
                ticket_id, answer = parse_answer(query)
            except InvalidAnswerError:
                bot_response = "Invalid answer format"
                bot_handler.send_reply(message, bot_response)
                return
            bot_response = f"Incident {ticket_id}\n status = {answer}"
            bot_handler.send_reply(message, bot_response)
        else:
            bot_response = 'type "new <description>" for a new incident'
            bot_handler.send_reply(message, bot_response)


def start_new_incident(query: str, message: Dict[str, Any], bot_handler: BotHandler) -> None:
    # Here is where we would enter the incident in some sort of backend
    # system.  We just simulate everything by having an incident id that
    # we generate here.

    incident = query[len("new ") :]

    ticket_id = generate_ticket_id(bot_handler.storage)
    bot_response = format_incident_for_markdown(ticket_id, incident)
    widget_content = format_incident_for_widget(ticket_id, incident)

    bot_handler.send_reply(message, bot_response, widget_content)


def parse_answer(query: str) -> Tuple[str, str]:
    m = re.match(r"answer\s+(TICKET....)\s+(.)", query)
    if not m:
        raise InvalidAnswerError

    ticket_id = m.group(1)

    # In a real world system, we'd validate the ticket_id against
    # a backend system.  (You could use Zulip itself to store incident
    # data, if you want something really lite, but there are plenty
    # of systems that specialize in incident management.)

    answer = m.group(2).upper()
    if answer not in "1234":
        raise InvalidAnswerError

    return (ticket_id, ANSWERS[answer])


def generate_ticket_id(storage: Any) -> str:
    try:
        incident_num = storage.get("ticket_id")
    except KeyError:
        incident_num = 0
    incident_num += 1
    incident_num = incident_num % 1000
    storage.put("ticket_id", incident_num)
    ticket_id = "TICKET%04d" % (incident_num,)
    return ticket_id


def format_incident_for_widget(ticket_id: str, incident: Dict[str, Any]) -> str:
    widget_type = "zform"

    heading = ticket_id + ": " + incident

    def get_choice(code: str) -> Dict[str, str]:
        answer = ANSWERS[code]
        reply = "answer " + ticket_id + " " + code

        return dict(
            type="multiple_choice",
            short_name=code,
            long_name=answer,
            reply=reply,
        )

    choices = [get_choice(code) for code in "1234"]

    extra_data = dict(
        type="choices",
        heading=heading,
        choices=choices,
    )

    widget_content = dict(
        widget_type=widget_type,
        extra_data=extra_data,
    )
    payload = json.dumps(widget_content)
    return payload


def format_incident_for_markdown(ticket_id: str, incident: Dict[str, Any]) -> str:
    answer_list = "\n".join(f"* **{code}** {ANSWERS[code]}" for code in "1234")
    how_to_respond = f"""**reply**: answer {ticket_id} <code>"""

    content = f"""
Incident: {incident}
Q: {QUESTION}

{answer_list}
{how_to_respond}"""
    return content


handler_class = IncidentHandler
