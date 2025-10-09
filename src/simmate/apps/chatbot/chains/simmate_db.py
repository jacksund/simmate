# -*- coding: utf-8 -*-

from langchain.chains.base import Chain
from langchain.prompts.prompt import PromptTemplate
from langchain_community.utilities import SQLDatabase
from langchain_community.utilities.sql_database import truncate_word
from langchain_core.output_parsers.list import CommaSeparatedListOutputParser
from langchain_experimental.sql import SQLDatabaseSequentialChain

from simmate.configuration import settings
from simmate.database.utilities import get_all_table_docs

from ..utilities import get_llm

# These are slow to load, so we store it as a global constant
DATABASE_METADATA = get_all_table_docs(include_empties=True)


class SimmateSQLDatabase(SQLDatabase):

    def get_table_info(self, table_names: list[str] = None) -> str:
        """
        Takes the default table info and adds simmate metadata docs to it, which
        includes things like the table and column definitions
        """

        base_string = super().get_table_info(table_names)

        patched_string = (
            "\n\nHere are extra docs on the tables listed above and their columns:\n"
        )
        for table_name in table_names:
            table_docs = DATABASE_METADATA.get(table_name)
            if table_docs:
                patched_string += f"DOCS FOR TABLE '{table_name}':\n"
                patched_string += f"{table_docs}\n\n"
        return base_string + patched_string


class PatchedSQLDatabase(SimmateSQLDatabase):
    """
    SQLDatabase returns the query result as a string. However, when
    return_direct=True on the chain/agent/tool, we want to return a dataframe
    instead. Rather than parse the string, it's more performant to override
    the `run` method of this class.
    """

    def run(
        self,
        command,
        fetch="all",
        include_columns=True,  # !!! default in langchain is False
        *,
        parameters=None,
        execution_options=None,
    ):
        """Execute a SQL command and return a string representing the results.

        If the statement returns rows, a string of the results is returned.
        If the statement returns no rows, an empty string is returned.
        """
        result = self._execute(
            command,
            fetch,
            parameters=parameters,
            execution_options=execution_options,
        )

        if fetch == "cursor":
            return result

        res = [
            {
                column: truncate_word(value, length=self._max_string_length)
                for column, value in r.items()
            }
            for r in result
        ]

        if not include_columns:
            res = [tuple(row.values()) for row in res]  # type: ignore[misc]

        # !!! All code above is unchanged. Below we just return the result,
        # rather than convert it to a string
        return res


def get_sql_chain(return_direct: bool = False, **kwargs) -> Chain:

    db_class = SimmateSQLDatabase if not return_direct else PatchedSQLDatabase

    db = db_class.from_uri(
        settings.chatbot.sql_uri,
        # we include only some tables to save tokens in the prompt
        # include_tables=get_all_table_names(), # if we wanted everything
        ignore_tables=[
            "authtoken_token",
            "chatbot_chatbothistory",
        ],
        # optionally we can include sample data in the prompt to help
        sample_rows_in_table_info=5,  # default is 3
        # This kwarg overrides table_info completely, so we use get_table_info instead
        # custom_table_info=DATABASE_METADATA,
    )
    llm = get_llm()

    # we use sequential chain isntead of SQLDatabaseChain because it reduces total
    # token use when we have many tables (and Simmate db has a lot)
    db_chain = SQLDatabaseSequentialChain.from_llm(
        llm,
        db,
        use_query_checker=True,  # DISABLE FOR SPEEDUP
        decider_prompt=DECIDER_PROMPT,
        query_prompt=POSTGRES_PROMPT,
        query_checker_prompt=QUERY_CHECKER_PROMPT,
        return_direct=return_direct,  # give the dataframe instead of a text response
        **kwargs,
        # common kwargs to use:
        #   verbose=True,
        #   top_k=10, # max number of rows any SQL query can respond with
    )

    return db_chain


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
    input_variables=["query", "table_names"],
    template=_decider_template,
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
    input_variables=["input", "table_info", "top_k"],
    template=_postgres_template,
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

# BUG: the connection closes on these... So I make utils to grab them instead
#
# ask_db_chain = get_sql_chain(
#     top_k=10,
#     verbose=True,
# )
# data_from_db_chain = get_sql_chain(
#     top_k=1000,
#     return_direct=True,
#     verbose=True,
# )

# OPTIMIZE: I need to figure out reasonable top_k values to use in prod


def get_ask_db_chain():
    return get_sql_chain(
        top_k=10,
        verbose=settings.chatbot.verbose,
    )


def get_data_from_db_chain():
    return get_sql_chain(
        top_k=1000,
        return_direct=True,
        verbose=settings.chatbot.verbose,
    )
