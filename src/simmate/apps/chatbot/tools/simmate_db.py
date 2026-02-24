# -*- coding: utf-8 -*-

import pandas as pd
from langchain.prompts.prompt import PromptTemplate
from langchain.tools import tool
from langchain_community.utilities import SQLDatabase
from langchain_community.utilities.sql_database import truncate_word
from langchain_core.output_parsers.list import CommaSeparatedListOutputParser
from langchain_experimental.sql import SQLDatabaseSequentialChain

from simmate.configuration import settings
from simmate.database.utilities import get_all_table_docs

from ..llm import get_llm

DATABASE_METADATA = get_all_table_docs(include_empties=True)
EXCLUDED_TABLES = ["authtoken_token", "chatbot_chatbothistory"]


class SimmateSQLDatabase(SQLDatabase):
    """
    Enhanced SQLDatabase that supports Simmate metadata injection
    and direct DataFrame-ready output.
    """

    def get_table_info(self, table_names: list[str] = None) -> str:
        base_string = super().get_table_info(table_names)
        if not table_names:
            return base_string

        metadata_parts = ["\n\nHere are extra docs on the tables and columns:\n"]
        for table_name in table_names:
            if table_docs := DATABASE_METADATA.get(table_name):
                metadata_parts.append(f"DOCS FOR TABLE '{table_name}':\n{table_docs}\n")

        return base_string + "\n".join(metadata_parts)

    def run(self, command: str, fetch: str = "all", return_raw: bool = False, **kwargs):
        """
        Modified run to optionally return a list of dicts (for DataFrames)
        instead of a formatted string.
        """
        # Ensure column names are included for DataFrame conversion
        kwargs["include_columns"] = True

        result = self._execute(command, fetch, **kwargs)
        if fetch == "cursor":
            return result

        # Process results with truncation logic from parent
        processed = [
            {k: truncate_word(v, length=self._max_string_length) for k, v in r.items()}
            for r in result
        ]

        return processed if return_raw else str(processed)


# -----------------------------------------------------------------------------


def get_sql_chain(return_direct: bool = False, top_k: int = 10):
    """
    Factory to create SQL chains with specific Simmate configurations.
    """
    db = SimmateSQLDatabase.from_uri(
        settings.chatbot.sql_uri,
        ignore_tables=EXCLUDED_TABLES,
        sample_rows_in_table_info=5,
    )

    return SQLDatabaseSequentialChain.from_llm(
        llm=get_llm(),
        db=db,
        query_checker_prompt=QUERY_CHECKER_PROMPT,
        decider_prompt=DECIDER_PROMPT,
        query_prompt=POSTGRES_PROMPT,
        use_query_checker=True,
        return_direct=return_direct,
        verbose=settings.chatbot.verbose,
        top_k=top_k,
    )


# -----------------------------------------------------------------------------


@tool(return_direct=True)
def get_dataframe_from_database(question: str) -> pd.DataFrame:
    """
    Load a dataset from the Simmate database as a DataFrame.
    Use for: loading datasets, exploratory data analysis.
    Do NOT use for: simple counts or metadata summaries.
    """
    chain = get_sql_chain(return_direct=True, top_k=1000)
    # The patched .run() returns the list of dicts, which DF accepts directly
    result = chain.run(question)
    return pd.DataFrame(result)


@tool
def get_answer_from_database(question: str) -> str:
    """
    Answer questions about Simmate data (counts, metadata, specific facts).
    Best for single-query questions.
    """
    chain = get_sql_chain(return_direct=False, top_k=10)
    return chain.run(question)


# -----------------------------------------------------------------------------
# All prompts below have been forked from...
#   from langchain_community.tools.sql_database.prompt
# -----------------------------------------------------------------------------

_decider_template = """
Given the below input question and list of potential tables, output a comma separated list of the table names that may be necessary to answer this question. Make sure to include a single space after each comma.

Question: {query}

Table Names: {table_names}

Relevant Table Names:
"""

DECIDER_PROMPT = PromptTemplate(
    template=_decider_template,
    input_variables=["query", "table_names"],
    output_parser=CommaSeparatedListOutputParser(),
)

# -----------------------------------------------------------------------------

_postgres_template = """
You are a PostgreSQL expert. Given an input question, first create a syntactically correct PostgreSQL query to run, then look at the results of the query and return the answer to the input question.
Unless the user specifies in the question a specific number of examples to obtain, query for at most {top_k} results using the LIMIT clause as per PostgreSQL. You can order the results to return the most informative data in the database.
Never query for all columns from a table. You must query only the columns that are needed to answer the question. Wrap each column name in double quotes (") to denote them as delimited identifiers.
Pay attention to use only the column names you can see in the tables below. Be careful to not query for columns that do not exist. Also, pay attention to which column is in which table.
Pay attention to use CURRENT_DATE function to get the current date, if the question involves "today".

Use the following format:

Question: Question here
SQLQuery: SQL Query to run
SQLResult: Result of the SQLQuery
Answer: Final answer here

Only use the following tables:
{table_info}

Use the following extra notes:
- In general, avoid using the 'molecule' and 'molecule_original' columns unless you are specifically asked for the sdf format of the molecule. Instead, when users want you to grab molecules, give them the `smiles` column as it is smaller and contains the same information.
- When asked to count the number of molecules, you can assume all entries in the table have a distinct `molecule`. Therefore, you can count the number of rows using `COUNT(*)`
- When users are involved, give their `first_name` and `last_name` from the related `auth_user` table as this is more helpful than their user `id` and `username`


Question: {input}
"""
# Note: Simmate auto-docs are pasted along with the "table_info" section as well

POSTGRES_PROMPT = PromptTemplate(
    template=_postgres_template,
    input_variables=["input", "table_info", "top_k"],
)

# -----------------------------------------------------------------------------

_query_checker_template = """
{query}

Double check the {dialect} query above for common mistakes, including:
- Using NOT IN with NULL values
- Using UNION when UNION ALL should have been used
- Using BETWEEN for exclusive ranges
- Data type mismatch in predicates
- Properly quoting identifiers
- Using the correct number of arguments for functions
- Casting to the correct data type
- Using the proper columns for joins

If there are any of the above mistakes, rewrite the query. If there are no mistakes, just reproduce the original query.

Output the final SQL query only. Do not wrap the query in a codeblock.

SQL Query: 
"""
QUERY_CHECKER_PROMPT = PromptTemplate(
    template=_query_checker_template,
    input_variables=["query", "dialect"],
)

# -----------------------------------------------------------------------------
