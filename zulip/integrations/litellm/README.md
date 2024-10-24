# Summarize topic

Generate a short summary of the last 100 messages in the provided topic URL.

### API Keys

For testing you need access token from
https://huggingface.co/settings/tokens (or set the correct env
variable with the access token if using a different model)

In `~/.zuliprc` add a section named `litellm` and set the api key for
the model you are trying to use.  For example:

```
[litellm]
HUGGINGFACE_API_KEY=YOUR_API_KEY
```

### Setup

```bash
$ pip install -r zulip/integrations/litellm/requirements.txt
```

Just run `zulip/integrations/litellm/summarize-topic` to generate
sample summary.

```bash
$ zulip/integrations/litellm/summarize-topic --help
usage: summarize-topic [-h] [--url URL] [--model MODEL]

options:
  -h, --help     show this help message and exit
  --url URL      The URL to fetch content from
  --model MODEL  The model name to use for summarization
```
