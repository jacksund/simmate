# -*- coding: utf-8 -*-

import unicodedata
import warnings

import requests
from bs4 import BeautifulSoup


class WebScraper:

    @staticmethod
    def get_html(url: str) -> BeautifulSoup:
        """
        Given a website URL, this will load the HTML and return a BeautifulSoup
        object for further workup.
        """

        # BUG: disable verify bc of SSL & silence warnings from not
        # using the verify fxn
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            response = requests.get(url, verify=False)

        if response.status_code == 200:
            html_content = response.text
        else:
            raise Exception(
                f"Failed to retrieve the page. Status code: {response.status_code}"
            )

        return BeautifulSoup(html_content, "html.parser")

    # TODO: add helper methods for parsing data using an LLM + prompts. See
    # the `apps.bcpc` for the start of this & example use

    @staticmethod
    def replace_accents(text: str) -> str:
        # replacements = {
        #     "é": "e",
        #     "è": "e",
        #     "ê": "e",
        #     "ë": "e",
        #     "á": "a",
        #     "à": "a",
        #     "ä": "a",
        #     "â": "a",
        #     "ç": "c",
        #     "í": "i",
        #     "ï": "i",
        #     "ò": "o",
        #     "ó": "o",
        #     "ô": "o",
        #     "ö": "o",
        #     "ú": "u",
        #     "ù": "u",
        #     "ü": "u",
        #     "–": "-",
        # }
        # for accented_char, replacement in replacements.items():
        #     text = text.replace(accented_char, replacement)
        # return text

        # This is a more robust implentation given by GPT. It should be effectively
        # the same as the commented out code above.
        nfkd_form = unicodedata.normalize("NFKD", text)
        nfkd_form = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
        return nfkd_form.encode("ascii", "ignore").decode("ascii")
