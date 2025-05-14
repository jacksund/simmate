# -*- coding: utf-8 -*-

from django.contrib.auth.backends import ModelBackend
from django.core.exceptions import PermissionDenied

from simmate.website.core_components.models import ApiToken

# Header encoding (see RFC5987)
HTTP_HEADER_ENCODING = "iso-8859-1"


class TokenAuthenticationMiddleware:
    """
    Middleware to authenticate requests using an API Token.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        # If the user is not already authenticated, try token authentication
        if not request.user.is_authenticated:
            token_auth = TokenAuthentication()
            user_auth_tuple = token_auth.authenticate(request)
            if user_auth_tuple:
                user, token = user_auth_tuple
                request.user = user

        # Continue processing as usual
        response = self.get_response(request)
        return response


class TokenAuthentication(ModelBackend):
    """
    Simple token based authentication.

    Clients should authenticate by passing the token key in the "Authorization"
    HTTP header, prepended with the string "Token ".  For example:

        Authorization: Token 401f7ac837da42b97f613d789819ff93537bee6a

    This is forked from rest_framework's TokenAuthentication class
    """

    # note: we inherit from ModelBackend instead of BaseBackend because we
    # want all user permissions + extra methods to be the same. It's only
    # the `authenticate` method that is overwritten

    keyword = "Token"

    def authenticate(self, request):

        # Gran the request's 'Authorization:' header, as a bytestring.
        auth = request.META.get("HTTP_AUTHORIZATION", b"")
        if isinstance(auth, str):
            auth = auth.encode(HTTP_HEADER_ENCODING)
        auth = auth.split()

        # make sure the header is present and it has the proper keyword leading.
        # If not, exit the auth process
        if not auth or auth[0].lower() != self.keyword.lower().encode():
            return None

        # Try to pull the token out from the header
        if len(auth) == 1:
            raise PermissionDenied("Invalid token header. No credentials provided.")
        elif len(auth) > 2:
            raise PermissionDenied(
                "Invalid token header. Token string should not contain spaces."
            )
        else:
            try:
                token_key = auth[1].decode()
            except UnicodeError:
                raise PermissionDenied(
                    "Invalid token header. Token string should not contain invalid characters."
                )

        # We now have a token and need to check if it's valid
        try:
            token = ApiToken.objects.select_related("user").get(key=token_key)
        except ApiToken.DoesNotExist:
            raise PermissionDenied("Invalid token.")

        if not token.user.is_active:
            raise PermissionDenied("User inactive or deleted.")

        return (token.user, token)
