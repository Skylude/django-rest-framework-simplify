import logging
import traceback
from typing import TypedDict

from django.http import Http404
from django.core.exceptions import PermissionDenied
from rest_framework import exceptions, status
from rest_framework.response import Response
from rest_framework.request import Request


class _Context(TypedDict):
    request: Request


def exception_handler(exc: Exception, context: _Context) -> Response:
    """
    exception_handler logs detailed exceptions and returns generic messages to consumers. The
    messages are vague for security reasons.

    Exceptions extending APIException are able to pass through messages with the default_detail
    field and status codes with the status_code field.

    Django's Http404 and PermissionDenied are translated to Rest Framework's NotFound and
    PermissionDenied.

    NotAuthenticated and AuthenticationFailed are coerced to a 403 status.
    """
    # Historically, 400 has been the default instead of 500.
    status_code = status.HTTP_400_BAD_REQUEST
    error_message = exceptions.APIException.default_detail

    exc = _django_to_rest_framework(exc)

    if isinstance(exc, exceptions.APIException):
        status_code = exc.status_code
        # default_detail is chosen over detail in order to not expose too much information.
        error_message = exc.default_detail

    _log_exception(exc, context, status_code, error_message)

    return Response(
        { 'errorMessage': error_message },
        status=status_code,
        content_type='application/json'
    )


def _django_to_rest_framework(exc):
    if isinstance(exc, Http404):
        return exceptions.NotFound()
    if isinstance(exc, PermissionDenied):
        return exceptions.PermissionDenied()
    return exc


def _log_exception(exc: Exception, context: _Context, status_code: int, error_message):
    last_frame, last_lineno = list(traceback.walk_tb(exc.__traceback__))[-1]
    exc_filename = last_frame.f_code.co_filename
    exc_lineno = last_lineno
    exc_func = last_frame.f_code.co_name

    logger = logging.getLogger('rest-framework-simplify-exception')
    extra = {
        'rq_query_params': context['request'].query_params,
        'rq_data': context['request'].data,
        'rq_method': context['request'].method,
        'rq_path': context['request'].path,
        'rs_status_code': status_code,
        'exc_filename': exc_filename,
        'exc_lineno': exc_lineno,
        'exc_func': exc_func,
        'exc_first_arg': exc.args[0] if exc.args else None,
        'exc_detail': exc.detail if isinstance(exc, exceptions.APIException) else None
    }
    logger.exception(error_message, extra=extra)
