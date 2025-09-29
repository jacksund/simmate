# -*- coding: utf-8 -*-

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render

from .component import HtmxComponent


def home(request):
    context = {
        "test": 1234,
    }
    template = "htmx/home.html"
    return render(request, template, context)


def component_call(
    request: HttpRequest,
    component_id: str,
    method_name: str = None,
) -> HttpResponse | JsonResponse:
    component = HtmxComponent.from_cache(component_id)
    if method_name:
        method = getattr(component, method_name)
        return method(request)
    else:
        return component.handle_request(request)
