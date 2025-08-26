# -*- coding: utf-8 -*-

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
