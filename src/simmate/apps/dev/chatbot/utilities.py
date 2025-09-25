# -*- coding: utf-8 -*-

import time

import streamlit
from langchain_openai import AzureChatOpenAI

from simmate.configuration import settings


def typewriter(text: str, speed: int):
    """
    Writes the most recent chatbot message using a typewriter effect.

    The original function is from:
       https://discuss.streamlit.io/t/st-write-typewritter/43111/2
    """
    tokens = text.split()
    container = streamlit.empty()
    for index in range(len(tokens) + 1):
        curr_full_text = " ".join(tokens[:index])
        container.markdown(curr_full_text)
        time.sleep(1 / speed)


def get_llm(temperature: float = 0.0, **kwargs) -> AzureChatOpenAI:
    """
    Inits LLM using Simmate config settings

    select model here:
    https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/models

    select version here:
    https://learn.microsoft.com/en-US/azure/ai-services/openai/reference

    Example settings:

    ``` yaml
    chatbot:
      endpoint: https://myendpoint.azure-api.net/
      model: gpt-4-turbo
      version: '2024-02-01'
      api_key: a1b2c3d4....
    ```

    Calling the model:

    ``` python
    from simmate.apps.dev.chatbot.utilities import get_llm

    llm = get_llm()
    response = llm.invoke("hello world!")
    ```
    """
    return AzureChatOpenAI(
        azure_endpoint=settings.chatbot.endpoint,
        azure_deployment=settings.chatbot.model,
        model_name=settings.chatbot.model,
        openai_api_version=settings.chatbot.version,
        openai_api_key=settings.chatbot.api_key,
        temperature=temperature,
        verbose=settings.chatbot.verbose,
        # callbacks=[langfuse_handler],  # no prod env yet
        **kwargs,
    )
