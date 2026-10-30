# Chatbot

--------------------------------------------------------------------------------

## About

The `chatbot` app connects Simmate to a large language model (LLM) using [LangChain](https://www.langchain.com/). It provides an agent with chemistry tools (e.g. looking up CAS numbers) and a table for storing chat history.

--------------------------------------------------------------------------------

## Installation

1. Add `chatbot` to the list of installed Simmate apps with:
``` bash
simmate config add chatbot
```

2. Install the chatbot dependencies in the same environment as Simmate:
``` bash
uv pip install "simmate[chatbot]"
```

3. Configure your LLM provider in `~/simmate/settings.yaml`. The supported providers are `OpenAI` (via Azure) and `Google-GenAI`. Any other keys are passed directly to the LLM client.
``` yaml
chatbot:
    provider: "Google-GenAI"
    model: "gemini-2.5-flash-lite"
    api_key: a1b2c3d4....
    temperature: 0
```

4. Update your database to include custom tables from the app:
``` shell
simmate database update
```

--------------------------------------------------------------------------------

## Basic Use

``` python
from simmate.apps.chatbot.agent import get_agent

agent = get_agent()
agent.invoke(
    {"messages": [{"role": "user", "content": "What is the CAS for aluminum oxide?"}]}
)
```

--------------------------------------------------------------------------------
