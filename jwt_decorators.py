import jwt
from flask import request, jsonify
from config import Config
from functools import wraps

def token_required(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        token = request.args.get('token')
        if not token:
            return jsonify({'Alert!': 'Token is missing!'})
        try:
            payload = jwt.decode(token, Config.JWT_SECRET_KEY)
        except:
            return jsonify({'Alert!':'Invalid Token!'})
    return decorated