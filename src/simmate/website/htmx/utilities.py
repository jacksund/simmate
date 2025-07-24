# -*- coding: utf-8 -*-

import uuid

from django.http import HttpResponse


def htmx_redirect(url: str) -> HttpResponse:
    response = HttpResponse()
    response["HX-Redirect"] = url
    return response


def get_uuid_starting_with_letter() -> str:
    # because the id is also used as html element ids, it must start with
    # a letter. We just generate uuids until we get one like that
    while True:
        u = uuid.uuid4()
        if u.hex[0].isalpha():
            return str(u)
