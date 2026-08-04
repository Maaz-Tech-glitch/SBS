from rest_framework.views import exception_handler
from rest_framework.response import Response
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        return response
    if isinstance(exc, ValueError):
        return Response({"error": str(exc)}, status=400)
    if isinstance(exc, (ObjectDoesNotExist, Http404)):
        return Response({"error": "Requested item not found."}, status=404)
    return Response(
        {"error": "Something went wrong. Please try again later."},
        status=500
    )