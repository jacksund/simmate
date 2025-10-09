# -*- coding: utf-8 -*-

import streamlit
from langchain.agents import AgentExecutor
from langchain.memory import ConversationBufferMemory
from langchain_community.chat_message_histories import StreamlitChatMessageHistory
from pandas import DataFrame
from PIL.PngImagePlugin import PngImageFile
from plotly.graph_objects import Figure

from simmate.configuration import settings
from simmate.database import connect

from .agent import simmate_agent
from .models import ChatbotHistory
from .tools import simmate_tools

# grab the user info from the URL parameters & authenticate
url_params = streamlit.query_params
user_id = url_params.get("user_id", None)
# api_key = url_params.get("api_key", None)  # TODO: for extra security
if not user_id:
    raise Exception("No user detected. Please authenticate")

# set up session state (memory) for the current user & their data
for key in ["images", "plots", "dataframes"]:
    if key not in streamlit.session_state:
        streamlit.session_state[key] = []

# for debugging
# streamlit.write(streamlit.session_state)

# Set up message memory
chat_history = StreamlitChatMessageHistory(key="chat_history")
memory = ConversationBufferMemory(chat_memory=chat_history)

# add welcome message if we have a new page
if len(chat_history.messages) == 0:
    chat_history.add_ai_message(
        "Hello! I am a chatbot that has been given tools to access & analyze "
        "chemical data. This includes all of the Simmate database. "
        "How can I help you?"
    )

# render all messages
for message in chat_history.messages:
    # not all messages are text! For example we can have images, plots, and tables.
    # These are represented with placeholder text. For example, an image would
    # be something like "(( IMAGE 2 ))" which means we can find the image object
    # at streamlit.session_state.images[2]

    chat_from = message.type
    content = message.content

    # all special non-string types start the same. Otherwise we have a string
    if not content.startswith("(("):
        streamlit.chat_message(chat_from).write(content)

    # otherwise we have a special type of the format "(( TYPE INDEX ))"
    else:
        content_type, content_index = (
            content.replace("((", "").replace("))", "").strip().split()
        )
        content_index = int(content_index)

        if content_type == "IMAGE":
            image = streamlit.session_state.images[content_index]
            streamlit.chat_message(chat_from).write(image)
        elif content_type == "DATAFRAME":
            dataframe = streamlit.session_state.dataframes[content_index]
            streamlit.chat_message(chat_from).write(dataframe)
        elif content_type == "PLOT":
            figure = streamlit.session_state.plots[content_index]
            streamlit.chat_message(chat_from).write(figure)
        else:
            raise Exception(f"Unknown message type! Message: {content}")

# Prompt the user for a new question/comment
user_message = streamlit.chat_input(placeholder="Ask a question!")

# When the user submits their question, trigger this section
if user_message:
    # store the new user message in the UI (note: it is added to history later)
    streamlit.chat_message("user").write(user_message)

    # Build the full LLM agent
    # OPTIMIZE: can I cache this for reuse?
    agent_executor = AgentExecutor(
        agent=simmate_agent,
        tools=simmate_tools,
        verbose=settings.chatbot.verbose,
    )

    # call the LLM api. This can be *very* slow so we add a spinner widget
    with streamlit.spinner("thinking & perfoming tasks..."):
        # TODO: use streamlit callback instead of my default spinner
        # from langchain_community.callbacks.streamlit import StreamlitCallbackHandler
        # with streamlit.chat_message("assistant"):
        # streamlit_callback = StreamlitCallbackHandler(streamlit.container())
        response = agent_executor.invoke(
            {
                "input": user_message,
                "chat_history": chat_history.messages,
            },
            # {"callbacks": [streamlit_callback]},
        )

    # regardless of what the output is, we can write it to the chat
    output = response["output"]
    streamlit.chat_message("assistant").write(output)

    # The output could be a number of things depending on what was asked:
    #
    #   1. text response from the chatbot
    #   2. PNG image (e.g, a molecule drawing or matplotlib render)
    #   3. pandas dataframe (e.g. output from a database query)
    #   4. plotly plot (e.g., output from analyzing a dataframe)
    #
    # The type tells us how to render it in streamlit. And regardless of the
    # type, we need to save the text/object to help on future calls
    if isinstance(output, str):
        ai_message = response["output"]

    elif isinstance(output, PngImageFile):
        streamlit.session_state.images.append(output)
        new_index = len(streamlit.session_state.images) - 1
        ai_message = f"(( IMAGE {new_index} ))"

    elif isinstance(output, DataFrame):
        streamlit.session_state.dataframes.append(output)
        new_index = len(streamlit.session_state.dataframes) - 1
        ai_message = f"(( DATAFRAME {new_index} ))"

    elif isinstance(output, Figure):
        streamlit.session_state.plots.append(output)
        new_index = len(streamlit.session_state.dataframes) - 1
        ai_message = f"(( PLOT {new_index} ))"

    elif output is None:
        ai_message = "(( failed attempt ))"

    else:
        raise Exception(f"Unknown agent response type: {type(output)}")

    # store the user's input and chatbot response in the history
    chat_history.add_user_message(user_message)
    chat_history.add_ai_message(ai_message)

    # save/update the history in the database
    streamlit.session_state["chat_id"] = ChatbotHistory.from_streamlit(
        chat_id=streamlit.session_state.get("chat_id", None),
        user_id=user_id,
        chat_history=chat_history,
    )
