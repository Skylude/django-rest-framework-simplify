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
