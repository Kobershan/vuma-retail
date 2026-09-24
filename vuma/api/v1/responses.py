from typing import Any


API_VERSION = "v1"


def success(
    data: Any = None,
    message: str | None = None,
    meta: dict | None = None,
):
    response = {
        "success": True,
        "api_version": API_VERSION,
        "data": data,
    }

    if message:
        response["message"] = message

    if meta:
        response["meta"] = meta

    return response


def failure(
    message: str,
    code: str = "VUMA_ERROR",
    data: Any = None,
):
    return {
        "success": False,
        "api_version": API_VERSION,
        "error": {
            "code": code,
            "message": message,
            "data": data,
        },
    }
