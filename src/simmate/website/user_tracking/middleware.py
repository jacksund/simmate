# -*- coding: utf-8 -*-

from simmate.website.utilities import parse_request_get

from .models import WebsitePageVisit


class WebsitePageVisitMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):

        # save a database entry for the page visit
        url_path = request.path
        url_parameters = parse_request_get(request)
        # note: we don't want to save AJAX requests (i.e. Django Unicorn)
        # because this is essentially tracking mouse clicks -- and would slow
        # down our dynamic pages.
        if not url_path.startswith("/message/"):
            visit = WebsitePageVisit(
                user=request.user,
                url_path=url_path,
                url_parameters=url_parameters,
            )
            visit.save()

        # Then process the request as you normally would
        response = self.get_response(request)
        return response
