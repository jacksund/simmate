# -*- coding: utf-8 -*-

import time

from langchain_core.language_models.chat_models import BaseChatModel

from simmate.configuration import settings


def typewriter(text: str, speed: int):
    """
    Writes the most recent chatbot message using a typewriter effect.

    The original function is from:
       https://discuss.streamlit.io/t/st-write-typewritter/43111/2
    """
    import streamlit

    tokens = text.split()
    container = streamlit.empty()
    for index in range(len(tokens) + 1):
        curr_full_text = " ".join(tokens[:index])
        container.markdown(curr_full_text)
        time.sleep(1 / speed)


def get_llm(**kwargs) -> BaseChatModel:
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
    from simmate.apps.chatbot.utilities import get_llm

    llm = get_llm()
    response = llm.invoke("hello world!")
    ```
    """

    # we 'pop' off some settings so we use a copy to modify
    llm_config = settings.chatbot.copy()
    provider = llm_config.pop("provider")

    llm_config.pop("sql_uri")  # not needed

    if provider == "OpenAI":
        try:
            from langchain_openai import AzureChatOpenAI
        except:
            Exception(
                "To use the chatbot with OpenAi, you must first run... "
                "`conda install -c conda-forge langchain-openai`"
            )

        return AzureChatOpenAI(
            **llm_config,
            # typical kwargs:
            # azure_endpoint
            # azure_endpoint
            # azure_deployment
            # model_name
            # openai_api_version
            # openai_api_key
            # temperature
        )

    elif provider == "Google-GenAI":
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
        except:
            Exception(
                "To use the chatbot with Google-GenAI, you must first run... "
                "`conda install -c conda-forge langchain-google-genai`"
            )

        llm = ChatGoogleGenerativeAI(
            **llm_config,
            # typical kwargs:
            # google_api_key
            # model
            # temperature
        )
        return llm

        # TODO:
        # enable url_context and google searching
        # tools = [
        #     {
        #         "url_context": {},
        #         "google_search": {},
        #     }
        # ]
        # llm_with_tools = llm.bind_tools(tools)
        # return llm_with_tools

    else:
        raise Exception(
            f"Unknown llm provider for chatbot: {provider}. "
            "Options are OpenAI and Google-GenAI"
        )
