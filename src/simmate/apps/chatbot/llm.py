# -*- coding: utf-8 -*-


from langchain_core.language_models.chat_models import BaseChatModel

from simmate.configuration import settings


def get_llm(**kwargs) -> BaseChatModel:
    """
    Connects to your large-language model (llm) using the config in the Simmate settings

    Example settings:
    ``` yaml
    chatbot:
        provider: "Google-GenAI"
        model: "gemini-2.5-flash-lite"
        api_key: a1b2c3d4....
        temperature: 0
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

        return ChatGoogleGenerativeAI(
            **llm_config,
            # typical kwargs:
            # google_api_key
            # model
            # temperature
        )

    else:
        raise Exception(
            f"Unknown llm provider for chatbot: {provider}. "
            "Options are OpenAI and Google-GenAI"
        )
