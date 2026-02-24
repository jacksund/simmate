# -*- coding: utf-8 -*-

from langchain.tools import tool
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.tools import DuckDuckGoSearchResults

from ..llm import get_llm

# NOTE: there is also the DuckDuckGoSearchRun which is better for very easy
# searches where you expect the answer to be shown right away. This is not
# good for searches where you need to open up URLs and double check things.
#   from langchain_community.tools import DuckDuckGoSearchRun

# NOTE: WebBaseLoader is minimal. Consider other doc loaders like
# UnstructuredURLLoader if I need more robust url loading at the cost of an
# extra dependency


@tool
def search_web_for_answer(question: str) -> dict:
    """Searches the web for context to answer a specific question.

    Args:
        question: The specific question to research and answer.
    """

    # 1. Perform web search and extract URLs
    search = DuckDuckGoSearchResults()
    # Access the wrapper directly to get a list of dictionaries with 'link' keys
    search_results = search.api_wrapper.results(question, max_results=3)
    urls = [result["link"] for result in search_results]

    if not urls:
        return {"answer": "No relevant search results found.", "sources": []}

    # 2. Pull web context using Unstructured
    loader = WebBaseLoader(urls)
    docs = loader.load()

    # Combine document contents into a single context string
    # We truncate to avoid exceeding model token limits
    context = "\n\n".join([doc.page_content.replace("\n", " ") for doc in docs])[
        :15_000
    ]
    # the replace() call removes a lot of the "fluff"

    # 3. Answer the question using the context
    llm = get_llm()
    prompt = (
        f"You are a helpful assistant. Answer the user's question using ONLY the provided context.\n\n"
        f"Question: {question}\n\n"
        f"Context:\n{context}"
    )
    response = llm.invoke(prompt)

    return {"answer": response.content, "sources": urls}
