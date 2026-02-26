from functools import wraps
from flask import request, jsonify

def validate_request(schema):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                data = schema().load(request.get_json())
                request.validated_data = data
            except Exception as err:
                return jsonify({"error": str(err)}), 400

            return fn(*args, **kwargs)
        return wrapper
    return decorator