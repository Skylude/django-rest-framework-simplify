import logging
import traceback
from typing import TypedDict

from rest_framework import status
from rest_framework.exceptions import APIException, NotAuthenticated, AuthenticationFailed
from rest_framework.response import Response
from rest_framework.request import Request


class _Context(TypedDict):
    request: Request


def exception_handler(exc: Exception, context: _Context) -> Response:
    status_code = status.HTTP_400_BAD_REQUEST
    error_message = APIException.default_detail

    if isinstance(exc, (NotAuthenticated, AuthenticationFailed)):
        status_code = status.HTTP_403_FORBIDDEN

    if exc.args:
        error_message = exc.args[0]

    # only want the last frame in generator
    exc_filename = None
    exc_lineno = None
    exc_func = None
    for frame, lineno in traceback.walk_tb(exc.__traceback__):
        exc_filename = frame.f_code.co_filename
        exc_lineno = lineno
        exc_func = frame.f_code.co_name

    logger = logging.getLogger('rest-framework-simplify-exception')
    extra = {
        'rq_query_params': context['request'].query_params.dict(),
        'rq_data': context['request'].data,
        'rq_method': context['request'].method,
        'rq_path': context['request'].path,
        'rs_status_code': status_code,
        'exc_filename': exc_filename,
        'exc_lineno': exc_lineno,
        'exc_func': exc_func
    }
    logger.error(error_message, extra=extra)

    return Response(
        { 'errorMessage': error_message },
        status=status_code,
        content_type='application/json'
    )
