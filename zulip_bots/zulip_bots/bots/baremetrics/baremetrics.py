# See readme.md for instructions on running this code.

from typing import Any, Dict, List

import requests

from zulip_bots.lib import BotHandler


class BaremetricsHandler:
    def initialize(self, bot_handler: BotHandler) -> None:
        self.config_info = bot_handler.get_config_info("baremetrics")
        self.api_key = self.config_info["api_key"]

        self.auth_header = {"Authorization": "Bearer " + self.api_key}

        self.commands = [
            "help",
            "list-commands",
            "account-info",
            "list-sources",
            "list-plans <source_id>",
            "list-customers <source_id>",
            "list-subscriptions <source_id>",
            "create-plan <source_id> <oid> <name> <currency> <amount> <interval> <interval_count>",
        ]

        self.descriptions = [
            "Display bot info",
            "Display the list of available commands",
            "Display the account info",
            "List the sources",
            "List the plans for the source",
            "List the customers in the source",
            "List the subscriptions in the source",
            "Create a plan in the given source",
        ]

        self.check_api_key(bot_handler)

    def check_api_key(self, bot_handler: BotHandler) -> None:
        url = "https://api.baremetrics.com/v1/account"
        test_query_response = requests.get(url, headers=self.auth_header)
        test_query_data = test_query_response.json()

        try:
            if test_query_data["error"] == "Unauthorized. Token not found (001)":
                bot_handler.quit("API Key not valid. Please see doc.md to find out how to get it.")
        except KeyError:
            pass

    def usage(self) -> str:
        return """
        This bot gives updates about customer behavior, financial performance, and analytics
        for an organization using the Baremetrics Api.\n
        Enter `list-commands` to show the list of available commands.
        Version 1.0
        """

    def handle_message(self, message: Dict[str, Any], bot_handler: BotHandler) -> None:
        content = message["content"].strip().split()

        if content == []:
            bot_handler.send_reply(message, "No Command Specified")
            return

        content[0] = content[0].lower()

        if content == ["help"]:
            bot_handler.send_reply(message, self.usage())
            return

        if content == ["list-commands"]:
            response = "**Available Commands:** \n"
            for command, description in zip(self.commands, self.descriptions):
                response += f" - {command} : {description}\n"

            bot_handler.send_reply(message, response)
            return

        response = self.generate_response(content)
        bot_handler.send_reply(message, response)

    def generate_response(self, commands: List[str]) -> str:
        try:
            instruction = commands[0]

            if instruction == "account-info":
                return self.get_account_info()

            if instruction == "list-sources":
                return self.get_sources()

            try:
                if instruction == "list-plans":
                    return self.get_plans(commands[1])

                if instruction == "list-customers":
                    return self.get_customers(commands[1])

                if instruction == "list-subscriptions":
                    return self.get_subscriptions(commands[1])

                if instruction == "create-plan":
                    if len(commands) == 8:
                        return self.create_plan(commands[1:])
                    else:
                        return "Invalid number of arguments."

            except IndexError:
                return "Missing Params."
        except KeyError:
            return "Invalid Response From API."

        return "Invalid Command."

    def get_account_info(self) -> str:
        url = "https://api.baremetrics.com/v1/account"
        account_response = requests.get(url, headers=self.auth_header)

        account_data = account_response.json()
        account_data = account_data["account"]

        template = [
            "**Your account information:**",
            "Id: {id}",
            "Company: {company}",
            "Default Currency: {currency}",
        ]

        return "\n".join(template).format(
            currency=account_data["default_currency"]["name"], **account_data
        )

    def get_sources(self) -> str:
        url = "https://api.baremetrics.com/v1/sources"
        sources_response = requests.get(url, headers=self.auth_header)

        sources_data = sources_response.json()
        sources_data = sources_data["sources"]

        response = "**Listing sources:** \n"
        for index, source in enumerate(sources_data):
            response += (
                "{_count}.ID: {id}\nProvider: {provider}\nProvider ID: {provider_id}\n\n"
            ).format(_count=index + 1, **source)

        return response

    def get_plans(self, source_id: str) -> str:
        url = f"https://api.baremetrics.com/v1/{source_id}/plans"
        plans_response = requests.get(url, headers=self.auth_header)

        plans_data = plans_response.json()
        plans_data = plans_data["plans"]

        template = "{_count}.Name: {name}\nActive: {active}\nInterval: {interval}\nInterval Count: {interval_count}\nAmounts:"
        response = ["**Listing plans:**"]
        for index, plan in enumerate(plans_data):
            response += (
                [template.format(_count=index + 1, **plan)]
                + [" - {amount} {currency}".format(**amount) for amount in plan["amounts"]]
                + [""]
            )

        return "\n".join(response)

    def get_customers(self, source_id: str) -> str:
        url = f"https://api.baremetrics.com/v1/{source_id}/customers"
        customers_response = requests.get(url, headers=self.auth_header)

        customers_data = customers_response.json()
        customers_data = customers_data["customers"]

        # FIXME BUG here? mismatch of name and display name?
        template = "{_count}.Name: {display_name}\nDisplay Name: {name}\nOID: {oid}\nActive: {is_active}\nEmail: {email}\nNotes: {notes}\nCurrent Plans:"
        response = ["**Listing customers:**"]
        for index, customer in enumerate(customers_data):
            response += (
                [template.format(_count=index + 1, **customer)]
                + [" - {name}".format(**plan) for plan in customer["current_plans"]]
                + [""]
            )

        return "\n".join(response)

    def get_subscriptions(self, source_id: str) -> str:
        url = f"https://api.baremetrics.com/v1/{source_id}/subscriptions"
        subscriptions_response = requests.get(url, headers=self.auth_header)

        subscriptions_data = subscriptions_response.json()
        subscriptions_data = subscriptions_data["subscriptions"]

        template = "{_count}.Customer Name: {name}\nCustomer Display Name: {display_name}\nCustomer OID: {oid}\nCustomer Email: {email}\nActive: {_active}\nPlan Name: {_plan_name}\nPlan Amounts:"
        response = ["**Listing subscriptions:**"]
        for index, subscription in enumerate(subscriptions_data):
            response += (
                [
                    template.format(
                        _count=index + 1,
                        _active=subscription["active"],
                        _plan_name=subscription["plan"]["name"],
                        **subscription["customer"],
                    )
                ]
                + [
                    " - {amount} {symbol}".format(**amount)
                    for amount in subscription["plan"]["amounts"]
                ]
                + [""]
            )

        return "\n".join(response)

    def create_plan(self, parameters: List[str]) -> str:
        data_header: Any = {
            "oid": parameters[1],
            "name": parameters[2],
            "currency": parameters[3],
            "amount": int(parameters[4]),
            "interval": parameters[5],
            "interval_count": int(parameters[6]),
        }

        url = f"https://api.baremetrics.com/v1/{parameters[0]}/plans"
        create_plan_response = requests.post(url, data=data_header, headers=self.auth_header)
        if "error" not in create_plan_response.json():
            return "Plan Created."
        else:
            return "Invalid Arguments Error."


handler_class = BaremetricsHandler
