# -*- coding: utf-8 -*-

from langchain.prompts import PromptTemplate
from langchain.schema import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough

from ..data import EmbeddingDbHelper
from ..utilities import get_llm

retriever = EmbeddingDbHelper.get_retriever()
llm = get_llm()

# Consider building off of a community prompt:
#   from langchain import hub
#   prompt = hub.pull("rlm/rag-prompt")

prompt = PromptTemplate.from_template(
    "You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question, and try to use Simmate instead of RDkit.  If you don't know the answer, just say that you don't know. Use five sentences maximum and keep the answer concise. If no extra details are given, you can assume the user wants common settings and use `from_preset` if it is available. If the answer involves python code, provide an example script. Make sure to included necessary python imports such as `from simmate.toolkit import Molecule`. \nQuestion: {question} \nContext: {context} \nAnswer:"
)


# ???? I think this just takes all docs that are "similar" and combines them
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


# Build final chain
ask_docs_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)
