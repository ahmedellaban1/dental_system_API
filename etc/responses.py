from rest_framework.response import Response
from rest_framework import status


def success(message="Success", data=None, code=status.HTTP_200_OK):
    return Response({
        "status": "success",
        "message": message,
        "data": data
    }, status=code)


def created(message="Created successfully", data=None):
    return Response({
        "status": "success",
        "message": message,
        "data": data
    }, status=status.HTTP_201_CREATED)


def bad_request(message="Invalid request", errors=None):
    return Response({
        "status": "error",
        "message": message,
        "errors": errors
    }, status=status.HTTP_400_BAD_REQUEST)


def unauthorized(message="Authentication required"):
    return Response({
        "status": "error",
        "message": message,
    }, status=status.HTTP_401_UNAUTHORIZED)


def forbidden(message="You do not have permission for this action"):
    return Response({
        "status": "error",
        "message": message,
    }, status=status.HTTP_403_FORBIDDEN)


def not_found(message="Resource not found"):
    return Response({
        "status": "error",
        "message": message,
    }, status=status.HTTP_404_NOT_FOUND)


def server_error(message="Internal server error"):
    return Response({
        "status": "error",
        "message": message,
    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
