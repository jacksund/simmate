# -*- coding: utf-8 -*-

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render

from .components import HtmxComponent


def home(request):
    context = {}
    template = "htmx/home.html"
    return render(request, template, context)


def component_call(
    request: HttpRequest,
    component_id: str,
    method_name: str = None,
) -> HttpResponse | JsonResponse:
    component = HtmxComponent.from_cache(component_id)
    return component.handle_request(request, method_name)
