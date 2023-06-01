import configparser
import csv
import os
import sys
from typing import Any, Dict

from langchain import LLMChain, PromptTemplate
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.chains import ConversationChain
from langchain.chains.conversation.memory import ConversationSummaryBufferMemory

import zulip


# Taken from https://github.com/f/awesome-chatgpt-prompts/blob/main/prompts.csv
def read_awesome_chatgpt_prompts():
    prompts = {}
    with open("prompts.csv") as f:
        reader = csv.reader(f)
        # Skip header
        next(reader)
        for row in reader:
            key = row[0].lower().replace(" ", "_")
            prompts[key] = row[1]
    return prompts


def initialize_llm(framework: str, token: str) -> None:
    if framework == "llama.cpp":
        from langchain.llms import LlamaCpp

        # Callbacks support token-wise streaming
        callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])
        # Verbose is required to pass to the callback manager
        model_path = "./guanaco-7B.ggmlv3.q4_0.bin"
        # Make sure the model path is correct for your system!
        return LlamaCpp(model_path=model_path, callback_manager=callback_manager, verbose=True)
    elif framework == "Hugging Face Hub":
        from langchain import HuggingFaceHub

        os.environ["HUGGINGFACEHUB_API_TOKEN"] = token

        repo_id = "google/flan-t5-xxl"
        repo_id = "stabilityai/stablelm-tuned-alpha-7b"
        # Low token output
        # repo_id = "timdettmers/guanaco-33b-merged"
        # Terse but not truncated
        repo_id = "bigscience/bloom"
        # Truncated, terse
        # repo_id = "tiiuae/falcon-7b-instruct"
        # Truncated, terse
        # repo_id = "tiiuae/falcon-7b"
        # Truncated, terse, wrong
        # repo_id = "OpenAssistant/oasst-sft-4-pythia-12b-epoch-3.5"
        # repo_id = "EleutherAI/gpt-neox-20b"
        return HuggingFaceHub(repo_id=repo_id, model_kwargs={"temperature": 0.1, "max_length": 512})
    else:
        if framework != "OpenAI":
            raise Exception(f"Framework {framework} not supported")
        from langchain.llms import OpenAI

        os.environ["OPENAI_API_KEY"] = token
        return OpenAI()


class LangChainZulip:
    def __init__(self, config_file: str, enable_conversational_memory: bool = False) -> None:
        self.template = """Question: {question}

Answer: Let's work this out in a step by step way to be sure we have the right answer."""
        self.prompt = PromptTemplate(template=self.template, input_variables=["question"])
        self.awesome_chatgpt_prompts = read_awesome_chatgpt_prompts()

        config: configparser.ConfigParser = configparser.ConfigParser()
        config.read(config_file)
        config_dict = dict(config["langchain"])
        zulip_config = dict(config["zulip"])

        self.zulip_client = zulip.Client(
            email=zulip_config["email"],
            api_key=zulip_config["key"],
            site=zulip_config["site"],
        )

        framework = config_dict.get("framework", "OpenAI")
        token = config_dict["token"]
        self.bot_name = config_dict["bot_name"]

        self.llm = initialize_llm(framework, token)
        if enable_conversational_memory:
            # https://www.pinecone.io/learn/langchain-conversational-memory/
            self.conversation_memory = ConversationSummaryBufferMemory(
                llm=self.llm, max_token_limit=650
            )
            self.llm_chain = ConversationChain(llm=self.llm, memory=self.conversation_memory)
        else:
            self.llm_chain = LLMChain(prompt=self.prompt, llm=self.llm)

    def process_message(self, message: str) -> None:
        at_mention = f"@**{self.bot_name}**"

        def startswith(prefix: str) -> bool:
            return message.startswith(f"{at_mention} {prefix}")

        if startswith("!show_prompt"):
            return self.template
        elif startswith("!set_prompt"):
            template = message.replace(f"{at_mention} !set_prompt", "")
            self.template = template
            self.prompt = PromptTemplate(template=self.template, input_variables=["question"])
            return "Prompt updated!"
        elif startswith("!set_prompt_from_templates"):
            prompt_key = message.split()[2]
            return lcz.llm_chain.run(
                message.replace(prompt_key, self.awesome_chatgpt_proms[prompt_key])
            )
        elif startswith("!clear_memory"):
            self.llm_chain.memory.clear()
            return "Memory forgotten!"
        return lcz.llm_chain.run(message)


config_file = "./langchain.conf"
if len(sys.argv) > 1:
    config_file = sys.argv[1]
lcz = LangChainZulip(config_file, enable_conversational_memory=True)


def handle_message(msg: Dict[str, Any]) -> None:
    print("processing", msg)
    if msg["type"] != "stream":
        return

    message = msg["content"]
    content = lcz.process_message(message)
    request = {
        "type": "stream",
        "to": msg["display_recipient"],
        "topic": msg["subject"],
        "content": content,
    }
    print("sending", content)
    lcz.zulip_client.send_message(request)


def watch_messages() -> None:
    print("Watching for messages...")

    def handle_event(event: Dict[str, Any]) -> None:
        if "message" not in event:
            # ignore heartbeat events
            return
        handle_message(event["message"])

    # https://zulip.com/api/real-time-events
    narrow = [["is", "mentioned"]]
    lcz.zulip_client.call_on_each_event(
        handle_event, event_types=["message"], all_public_streams=True, narrow=narrow
    )


watch_messages()
