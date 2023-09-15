import jwt
import datetime
from config import Config

def generate_jwt_token(user_id):
    secret_key = Config.JWT_SECRET_KEY

    payload = {
        'sub': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }

    token = jwt.encode(payload, secret_key, algorithm='HS256')

    return token, secret_key
def get_user_id_from_token(token):
    try:
        payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=['HS256'])
        user_id = payload['sub']
        return user_id
    except jwt.ExpiredSignatureError:
        # Handle token expiration error here
        return None
    except jwt.InvalidTokenError:
        # Handle invalid token error here
        return None
