import logging
import shutil
from pathlib import Path

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_community.vectorstores import Chroma
from langchain_openai import AzureOpenAIEmbeddings


class EmbeddingDbHelper:
    """
    Experimental class for preparing vector/embedding databases for langchain use
    """

    data_file: str = "all_docs.zip"
    """
    File within this module that contains the raw data to be vectorized/embedded
    """

    @classmethod
    def get_retriever(cls):
        vectorstore = cls._get_vectorstore()
        retriever = vectorstore.as_retriever(
            search_type="similarity",  # or "mmr" or "similarity_score_threshold"
            search_kwargs=dict(
                k=4,  # number of documents returned
                # fetch_k=20,  # number of docs to pass to MMR alg
                # lambda_mult=0.5,  # diversity of results returned by MMR (1=min, 0=max diversity)
            ),
        )
        return retriever

    @classmethod
    def _get_vectorstore(cls):
        # Embed, store, and get retriever
        embedding = AzureOpenAIEmbeddings(azure_deployment="text-embedding-ada-002")

        # TODO: check for existing file & persist vectorstore
        # current_directory = Path(__file__).parent
        # datafile = current_directory / cls.data_file
        # collection_name = datafile.stem
        # # load from disk
        # vectorstore = Chroma(
        #     persist_directory="./chroma_db",
        #     embedding_function=embedding_function,
        # )

        # if it doesn't exist, create a new one
        documents = cls._get_documents()

        # Chroma prints a bunch of ugly SSL errors so we disable logging
        logger = logging.getLogger()
        logger.disabled = True

        vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=embedding,
            # collection_name=collection_name,
            # persist_directory=str(current_directory),
            # collection_metadata  # <-- is this useful?
        )

        # reactivate logging
        logger.disabled = False

        return vectorstore

    @classmethod
    def _get_documents(cls):
        # Grab the directory of this current python file
        current_directory = Path(__file__).parent

        # Set the full path to the data file
        datafile = current_directory / cls.data_file
        assert datafile.exists()

        # TODO: support inputs like CSV files. Currently I assume a zip file
        # with markdown files in it

        # if the files are stored in a zip file, uncompress the files to
        # a temporary directory (which we delete after reading)
        # if datafile.suffix == ".zip":
        extract_dir = Path.cwd() / datafile.stem
        shutil.unpack_archive(
            datafile,
            extract_dir=extract_dir,
        )

        loader = DirectoryLoader(
            extract_dir,
            recursive=True,
            # UnstructuredFileLoader autodetects & uses UnstructuredMarkdownLoader
            # OPTIMIZE: test this loader with a more advanced `format_docs` method
            # loader_cls=UnstructuredFileLoader,
            loader_cls=TextLoader,
            # Using 'elements' gives very small & detailed docs... but we need to
            # grab parent docs (i.e.) run multiple queries for this to be effective
            # loader_kwargs=dict(
            #     mode="elements",
            # ),
            show_progress=True,
            # Skip non-markdown files (e.g. svg or png)
            glob="**/*.md",
            # Parallelization: this is only really needed for >>100 files
            # use_multithreading=True,
            # max_concurrency=4,
            # For debugging
            # silent_errors=True,
        )

        # Load input docs
        docs = loader.load()

        # delete all files now that we are done loading them
        # shutil.rmtree(extract_dir)

        # BUG-FIX: the metadata values can only be certain types, but by default,
        # Unstructured is returning a list for the "languages" entries
        for doc in docs:
            if isinstance(doc.metadata.get("languages", None), list):
                doc.metadata.pop("languages")
                doc.metadata["language"] = "eng"

        # Further split any sections that are too big
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,
            chunk_overlap=300,
            add_start_index=True,
        )
        splits = text_splitter.split_documents(docs)

        # the "splits" are our final documents
        return splits
