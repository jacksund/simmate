# -*- coding: utf-8 -*-

from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an assistant that helps with cheminformatics and Simmate, but you don't know any of the needed information yourself. You need to always look up relevent data in the Simmate database before you can answer any questions. If you are unsure of what to answer, say 'I am unsure'.",
        ),
        MessagesPlaceholder(variable_name="chat_history"),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)
