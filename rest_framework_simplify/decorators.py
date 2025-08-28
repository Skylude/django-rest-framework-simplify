from functools import wraps


def sensitive_rq_data(*keys):
    """
    sensitive_rq_data decorates a view method to annotate raised exceptions with keys deemed
    sensitive to logging.

    These annotations are used in the rest_framework_simplify.handler.exception_handler to avoid
    including these keys in the rq_data extra on the exception log.

    Note the keys are compared as all lower with underscores removed.
    """
    def decorator(func):
        @wraps(func)
        def inner(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as ex:
                ex._sensitive_rq_data_keys = keys
                raise
        return inner
    return decorator


def sensitive_rq_query_params(*keys):
    """
    sensitive_rq_query_params decorates a view method to annotate raised exceptions with keys
    deemed sensitive to logging.

    These annotations are used in the rest_framework_simplify.handler.exception_handler to avoid
    including these keys in the rq_query_params extra on the exception log.

    Note the keys are compared as all lower with underscores removed.
    """
    def decorator(func):
        @wraps(func)
        def inner(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as ex:
                ex._sensitive_rq_query_params = keys
                raise
        return inner
    return decorator
