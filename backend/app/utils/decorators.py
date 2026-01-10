"""
Shared request/response decorators.
"""
from functools import wraps

from flask import jsonify, request


def limit_content_length(max_bytes: int):
    """Reject requests with a Content-Length above max_bytes."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            content_length = request.content_length
            if content_length is not None and content_length > max_bytes:
                return jsonify({
                    "error": "Request too large",
                    "max_bytes": max_bytes,
                }), 413
            return func(*args, **kwargs)
        return wrapper
    return decorator
