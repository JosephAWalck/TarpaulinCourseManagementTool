from flask import Flask, jsonify

from routes.users_routes import user_blueprint
from routes.courses_routes import courses_blueprint

from utils.verify_jwt import AuthError

app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    return "Welcome to the Tarpaulin Course Management API! Please refer to the documentation for API usage"

app.register_blueprint(user_blueprint, url_prefix='/users')
app.register_blueprint(courses_blueprint, url_prefix='/courses')

@app.errorhandler(AuthError)
def handle_auth_error(ex):
    response = jsonify(ex.error)
    response.status_code = ex.status_code
    return response

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)