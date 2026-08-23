from rest_framework.views import exception_handler
from rest_framework.response import Response
from users.exceptions import AppException


def custom_exception_handler(exc, context):

    if isinstance(exc, AppException):
        return Response({"error": exc.detail}, status=exc.status_code)
    response = exception_handler(exc, context)
    if response is not None:
        return response

    raise exc