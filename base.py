from flask import Flask, request, jsonify, render_template
import pymysql
from models import db, Model, Version, Feature
from jwtToken import generate_jwt_token
from jwt_decorators import token_required
from flask_jwt_extended import JWTManager, jwt_required, unset_jwt_cookies
from flask_jwt_extended import get_jwt,get_jwt_identity
import hashlib
from sqlalchemy import func

revoked_token_list = set()

app = Flask(__name__, static_folder="templates/static", template_folder="templates")

jwt_manager = JWTManager(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://abproto1:abpr0t01@ab-proto-1.cluster-cunq64theuzf.us-east-2.rds.amazonaws.com:3306/ab-proto1'
app.config.from_object('config.Config')
db.init_app(app)


def get_db_connection():
    host = 'ab-proto-1.cluster-cunq64theuzf.us-east-2.rds.amazonaws.com'
    user = 'abproto1'
    db_password = 'abpr0t01'
    database = 'ab-proto1'

    connection = pymysql.connect(host=host,
                                 user=user,
                                 password=db_password,
                                 database=database,
                                 port=3306,
                                 charset='utf8mb4',
                                 cursorclass=pymysql.cursors.DictCursor)
    return connection

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
  return render_template("index.html")


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    connection = get_db_connection()

    with connection:
        cur = connection.cursor()
        cur.execute("SELECT * FROM customer WHERE name=%s", (username,))
        user_data = cur.fetchone()

        if user_data:
            # Hash the provided password using SHA-256
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            # Compare the hashed password with the one stored in the database
            if hashed_password == user_data['auth_token']:
                token, secret_key = generate_jwt_token(user_data['id'])
                return jsonify({'message': 'Login successful!', 'access_token': token})

        # If no match or incorrect password, return an error message
        return jsonify({'message': 'Invalid username or password'})


def check_if_token_in_blocklist(jwt_header, jwt_payload):
    # Check if the token is in the blacklist here
    jti = jwt_payload['jti']
    return jti in revoked_token_list  # Assuming 'blacklist' is a set of revoked tokens



@app.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    jti = get_jwt()['jti']  # Get the unique identifier (jti) of the current token
    revoked_token_list.add(jti)  # Add the jti to the revoked token list
    unset_jwt_cookies(response=app.make_response(jsonify(message='Logout successful')))
    return jsonify(message='Logout successful')

@app.route('/register', methods=['GET'])
def register():
    username = request.args.get('username')
    password = request.args.get('password')

    if not username or not password:
        return jsonify({'message': 'Invalid username or password'})

    connection = get_db_connection()

    # Hash the password using SHA-256
    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    with connection:
        cur = connection.cursor()
        cur.execute("INSERT INTO customer (name, auth_token) VALUES (%s, %s)", (username, hashed_password))
        connection.commit()

    return jsonify({'message': 'User registered successfully!'})

@app.route('/login_form')
def login_form():
    return render_template('login_form.html')

# Route to handle POST request and return models and versions for a given customer_id
@app.route('/get_models_and_versions', methods=['GET'])
@jwt_required()
def get_models_and_versions():
    customer_id = get_jwt_identity()
    if not customer_id:
        return jsonify({'message': 'Invalid request. Please provide customer_id in the JSON data.'}), 400

        # Query the Model table to retrieve models for the given customer_id
    models = Model.query.filter_by(customer_id=customer_id).all()

    # Prepare the response JSON data
    response_data = {
        'customer_id': customer_id,
        'models': []
    }

    for model in models:
        model_data = {
            'id': model.id,
            'name': model.name,
            'type': model.type.value,
            'versions': []
        }

        # Query the Version table to retrieve versions for the current model
        versions = Version.query.filter_by(model_id=model.id).all()

        for version in versions:
            version_data = {
                'id': version.id,
                'number': version.number,
            }

            # Check if the timestamp is not None before adding it to the response
            if version.timestamp is not None:
                version_data['timestamp'] = version.timestamp.isoformat()

            model_data['versions'].append(version_data)

        response_data['models'].append(model_data)

    return jsonify(response_data), 200

@app.route('/get_insights/<int:version_id>', methods=['GET'])
@jwt_required()
def get_insights_for_version(version_id):
    version = Version.query.get(version_id)
    # Get the authenticated user's customer_id
    current_user = get_jwt_identity()
    if not version:
        return jsonify({'message': 'Version not found'}), 404
    model_id = version.model_id

    # Get the model's customer_id from the Model table
    model = Model.query.get(model_id)
    if not model:
        return jsonify({'message': 'Model not found'}), 404

    model_customer_id = model.customer_id
    # Check if the authenticated user's customer_id matches the model's customer_id
    if current_user != model_customer_id:
        return jsonify({'message': 'Unauthorized access'}), 401
    # Get insights data from the version's method
    insights_data = version.get_insights()

    # Get counts of categorical and feature types from the 'features' table
    categorical_count = db.session.query(func.count(Feature.id)).filter_by(type='categorical').scalar()
    feature_count = db.session.query(func.count(Feature.id)).filter_by(type='feature').scalar()

    # Include counts in the response
    response_data = {
        'version_id': version_id,
        'insights': insights_data,
        'categorical_count': categorical_count,
        'feature_count': feature_count
    }
    return jsonify(response_data), 200


if __name__ == '__main__':
    app.run(debug=False, port=5000)
