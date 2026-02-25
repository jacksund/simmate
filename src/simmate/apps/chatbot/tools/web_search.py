# -*- coding: utf-8 -*-

from langchain.tools import tool
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.tools import DuckDuckGoSearchResults

from ..llm import get_llm


@tool
def search_web_for_context(
    query: str,
    max_results: int = 5,
    page_trunc_limit: int = 15_000,
) -> dict:
    """
    Searches the web for context about a specific question and provides the
    loaded web pages for the top search results back as context.
    """

    # 1. Perform web search and extract URLs
    search = DuckDuckGoSearchResults()
    # Access the wrapper directly to get a list of dictionaries with 'link' keys
    search_results = search.api_wrapper.results(query, max_results=5)
    urls = [result["link"] for result in search_results]
    if not urls:
        return {"answer": "No relevant search results found.", "sources": []}
    # NOTE: there is also the DuckDuckGoSearchRun which is better for very easy
    # searches where you expect the answer to be shown right away. This is not
    # good for searches where you need to open up URLs and double check things.
    #   from langchain_community.tools import DuckDuckGoSearchRun

    # 2. Pull web context using Unstructured
    loader = WebBaseLoader(urls)
    docs = loader.load()
    # NOTE: WebBaseLoader is minimal. Consider other doc loaders like
    # UnstructuredURLLoader if I need more robust url loading at the cost of an
    # extra dependency

    # Combine document contents into a single context dict
    # We truncate to avoid exceeding model token limits
    # the replace() call removes a lot of the "fluff"
    context = [
        {
            "source_url": doc.metadata["source"],
            "title": doc.metadata.get("title", None),
            "page_content": doc.page_content.replace("\n", " ")[:page_trunc_limit],
        }
        for doc in docs
    ]
    # OPTIMIZE: it is likely better pull out relevent chunks via embedding/similarity

    return context


@tool
def search_web_for_answer(query: str) -> dict:
    """
    Searches the web for context to answer a specific question. Then provides
    an answer to that question using only the web context found.

    Use this instead of `search_web_for_context` when you only care about the
    answer and not the rest of the content
    """
    context = search_web_for_context(query)
    urls = [s["source_url"] for s in context]
    llm = get_llm()
    prompt = (
        f"You are a helpful assistant. Answer the user's question using ONLY the provided context.\n\n"
        f"Question: {query}\n\n"
        f"Context:\n{context}"
    )
    response = llm.invoke(prompt)

    return {"answer": response.content, "sources": urls}
