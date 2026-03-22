# -*- coding: utf-8 -*-

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnable import RunnablePassthrough
from langchain_core.tools import tool

from ..data import EmbeddingDbHelper
from ..utils import get_llm


@tool
def ask_simmate_docs(question: str) -> str:
    """
    Search the Simmate documentation for technical questions, Python examples,
    and common settings/presets. Use this tool for any queries regarding
    Simmate toolkit, database, workflow, and app-building usage.
    """

    retriever = EmbeddingDbHelper.get_retriever()
    llm = get_llm()

    prompt = PromptTemplate.from_template(
        "You are an assistant for question-answering tasks. Use the following pieces of "
        "retrieved context to answer the question, and try to use Simmate instead of RDkit. "
        "If you don't know the answer, just say that you don't know. Use five sentences "
        "maximum and keep the answer concise. If no extra details are given, you can "
        "assume the user wants common settings and use `from_preset` if it is available. "
        "If the answer involves python code, provide an example script. Make sure to "
        "include necessary python imports such as `from simmate.toolkit import Molecule`."
        "\n\nQuestion: {question} \nContext: {context} \nAnswer:"
    )

    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    # Build the internal chain
    chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    # Execute the chain and return the string result
    return chain.invoke(question)
