from typing import Optional

from rest_framework.exceptions import APIException


class ParseException(Exception):
    def __init__(self, ex):
        # Call the base class constructor with the parameters it needs
        if hasattr(ex, 'args') and len(ex.args) > 0:
            error_message = ex.args[0]
        else:
            error_message = ex
        super(ParseException, self).__init__(error_message)


class EmailTemplateException(Exception):
    def __init__(self, message):
        # Call the base class constructor with the parameters it needs
        super(EmailTemplateException, self).__init__(message)


class SimplifyAPIException(APIException):
    """
    SimplifyAPIException is an APIException that assigns the provided error_message to the
    default_detail. This is intended to work with the Simplify exception_handler since the handler
    returns uses default_detail instead of detail.
    """

    def __init__(self, error_message: Optional[str] = None, status_code: Optional[int] = None):
        """
        :param str error_message: error message to show in the response
        :param int status_code: status code associated with the response
        """
        if error_message is not None:
            self.default_detail = error_message
        if status_code is not None:
            self.status_code = status_code
        super().__init__()
