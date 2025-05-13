# -*- coding: utf-8 -*-

from django.contrib.auth.models import AnonymousUser

from simmate.website.utilities import parse_request_get

from ..models import WebsitePageVisit


class WebsitePageVisitMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):

        # save a database entry for the page visit
        url_path = request.path
        url_parameters = parse_request_get(request)
        user = request.user if not isinstance(request.user, AnonymousUser) else None

        # note: we don't want to save AJAX requests (i.e. Django Unicorn)
        # because this is essentially tracking mouse clicks -- and would slow
        # down our dynamic pages.
        excluded_urls = [
            "/unicorn/message/",
            # !!! TODO: account for other providers (e.g. google)
            "/accounts/microsoft/login/callback",
        ]
        if not any([url_path.startswith(u) for u in excluded_urls]):
            visit = WebsitePageVisit(
                user=user,
                url_path=url_path,
                url_parameters=url_parameters,
            )
            visit.save()

        # Then process the request as you normally would
        response = self.get_response(request)
        return response
