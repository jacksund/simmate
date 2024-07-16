# -*- coding: utf-8 -*-

from urllib import parse

from django.utils.encoding import force_str


def replace_query_param(url: str, key: str, val: any) -> str:
    """
    Given a URL and a key/val pair, set or replace an item in the query
    parameters of the URL, and return the new URL.

    This is forked from `rest_framework.utils.urls`
    """
    (scheme, netloc, path, query, fragment) = parse.urlsplit(force_str(url))
    query_dict = parse.parse_qs(query, keep_blank_values=True)
    query_dict[force_str(key)] = [force_str(val)]
    query = parse.urlencode(sorted(query_dict.items()), doseq=True)
    return parse.urlunsplit((scheme, netloc, path, query, fragment))


def remove_query_param(url: str, key: str) -> str:
    """
    Given a URL and a key/val pair, remove an item in the query
    parameters of the URL, and return the new URL.

    This is forked from `rest_framework.utils.urls`
    """
    (scheme, netloc, path, query, fragment) = parse.urlsplit(force_str(url))
    query_dict = parse.parse_qs(query, keep_blank_values=True)
    query_dict.pop(key, None)
    query = parse.urlencode(sorted(query_dict.items()), doseq=True)
    return parse.urlunsplit((scheme, netloc, path, query, fragment))


def get_pagination_urls(request, current_page) -> dict:
    # OPTIMIZE: not sure if there is a better way to do this...

    # Clean up current URL to ensure we have the page GET arg present
    current_url = request.get_full_path()  # to include GET params
    current_page_arg = f"page={current_page.number}"
    # no GET args set at all + page inferred
    if "/?" not in current_url:
        current_url += f"?{current_page_arg}"
    # other GET args set + page inferred
    elif current_page_arg not in current_url:
        current_url += f"&{current_page_arg}"

    # grab next/previous links (for arrow buttons)
    next_url = (
        replace_query_param(current_url, "page", current_page.next_page_number())
        if current_page.has_next()
        else None
    )
    previous_url = (
        replace_query_param(current_url, "page", current_page.previous_page_number())
        if current_page.has_previous()
        else None
    )

    # build out links
    elided_pages = current_page.paginator.get_elided_page_range(
        number=current_page.number,
        on_each_side=2,
        on_ends=1,
    )  # ex: [1, '…', 49, 50, 51, 52, 53, '…', 100] when current page is 51
    elided_pages = [
        (
            (page_number, replace_query_param(current_url, "page", page_number))
            if page_number != "..."
            else ("...", None)
        )
        for page_number in elided_pages
    ]

    return {
        "previous": previous_url,  # just url str
        "next": next_url,  # just url str
        "elided_pages": elided_pages,  # list of (display, url str)
    }
