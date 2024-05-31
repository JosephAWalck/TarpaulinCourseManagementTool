from flask import Flask, request, jsonify, send_file
from google.cloud import datastore, storage
from google.cloud.datastore import query
from google.cloud.datastore.query import PropertyFilter

import requests
import json
import io

from six.moves.urllib.request import urlopen
from jose import jwt
from authlib.integrations.flask_client import OAuth

app = Flask(__name__)
app.secret_key='SUPER_SECRET'
# app.secret_key = 'SECRET_KEY'

client = datastore.Client()

# constants
USERS='users'
COURSES='courses'
PHOTO_BUCKET='tarpaulin-course-management-tool'


# Update the values of the following 3 variables
CLIENT_ID = 'RufibzCFomegicWBS0YNhGjJY0YXt7pw'
CLIENT_SECRET = 'BFR5zHC9RRflB5N5FB2fcExYtpWDoqEsl5KFn27aOeS9KgD2bUu3vkqmNSEJXJlw'
DOMAIN = 'dev-mn363pj1o6m465xf.us.auth0.com'
# For example
# DOMAIN = '493-24-spring.us.auth0.com'
# Note: don't include the protocol in the value of the variable DOMAIN

ALGORITHMS = ["RS256"]

oauth = OAuth(app)

auth0 = oauth.register(
    'auth0',
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    api_base_url="https://" + DOMAIN,
    access_token_url="https://" + DOMAIN + "/oauth/token",
    authorize_url="https://" + DOMAIN + "/authorize",
    client_kwargs={
        'scope': 'openid profile email',
    },
)

# This code is adapted from https://auth0.com/docs/quickstart/backend/python/01-authorization?_ga=2.46956069.349333901.1589042886-466012638.1589042885#create-the-jwt-validation-decorator

class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


def verify_jwt(request, err_state=True):
    if 'Authorization' in request.headers:
        auth_header = request.headers['Authorization'].split()
        token = auth_header[1]
    else:
        if err_state:
            raise AuthError({"code": "no auth header",
                            "description":
                                "Authorization header is missing"}, 401)
        return None
    
    jsonurl = urlopen("https://"+ DOMAIN+"/.well-known/jwks.json")
    jwks = json.loads(jsonurl.read())
    try:
        unverified_header = jwt.get_unverified_header(token)
    except jwt.JWTError:
        if err_state:
            raise AuthError({"code": "invalid_header",
                            "description":
                                "Invalid header. "
                                "Use an RS256 signed JWT Access Token"}, 401)
        return None
    if unverified_header["alg"] == "HS256":
        if err_state:
            raise AuthError({"code": "invalid_header",
                            "description":
                                "Invalid header. "
                                "Use an RS256 signed JWT Access Token"}, 401)
        return None
    rsa_key = {}
    for key in jwks["keys"]:
        if key["kid"] == unverified_header["kid"]:
            rsa_key = {
                "kty": key["kty"],
                "kid": key["kid"],
                "use": key["use"],
                "n": key["n"],
                "e": key["e"]
            }
    if rsa_key:
        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=CLIENT_ID,
                issuer="https://"+ DOMAIN+"/"
            )
        except jwt.ExpiredSignatureError:
            if err_state:
                raise AuthError({"code": "token_expired",
                                "description": "token is expired"}, 401)
            return None
        except jwt.JWTClaimsError:
            if err_state:
                raise AuthError({"code": "invalid_claims",
                                "description":
                                    "incorrect claims,"
                                    " please check the audience and issuer"}, 401)
            return None
        except Exception:
            if err_state:
                raise AuthError({"code": "invalid_header",
                                "description":
                                    "Unable to parse authentication"
                                    " token."}, 401)
            return None

        return payload
    else:
        if err_state:
            raise AuthError({"code": "no_rsa_key",
                                "description":
                                    "No RSA key in JWKS"}, 401)
        return None

@app.route('/')
def index():
    return "Welcome to the Tarpaulin Course Management API! Please refer to the documentation for API usage"

@app.route('/' + USERS + '/login', methods=['POST'])
def login_user():
    content = request.get_json()
    keys = ['username', 'password']
    for k in keys:
        if not content.get(k):
            return {"Error": "The request body is invalid"}, 400
    username = content["username"]
    password = content["password"]
    body = {'grant_type':'password','username':username,
            'password':password,
            'client_id':CLIENT_ID,
            'client_secret':CLIENT_SECRET
           }
    headers = { 'content-type': 'application/json' }
    url = 'https://' + DOMAIN + '/oauth/token'
    r = requests.post(url, json=body, headers=headers)
    token = r.json()
    if token.get('error'):
        return {'Error': 'Unauthorized'}, 401
    return { "token": token['id_token'] }, 200, {'Content-Type':'application/json'}
        

# Decode the JWT supplied in the Authorization header
@app.route('/decode', methods=['GET'])
def decode_jwt():
    payload = verify_jwt(request)
    return payload     

@app.route('/' + USERS, methods=['GET'])
def get_all_users():
    payload = verify_jwt(request, False)
    query = client.query(kind=USERS)
    if payload:
        query.add_filter('sub', '=', payload['sub'])
        query.add_filter('role', '=', 'admin')
    else:
        return {'Error': 'Unauthorized'}, 401
    
    admin = list(query.fetch())
    if not admin:
        return {'Error': 'You don\'t have permission on this resource'}, 403
    query = client.query(kind=USERS)
    users = list(query.fetch())
    for u in users:
        u['id'] = u.key.id
    return users

@app.route('/' + USERS + '/<int:user_id>', methods=['GET'])
def get_user(user_id):
    payload = verify_jwt(request, False)
    if not payload:
        return {'Error': 'Unauthorized'}, 401
    user_key = client.key(USERS, user_id)
    user = client.get(key=user_key)
    if not user or payload['sub'] != user['sub']:
        return {'Error': 'You don\'t have permission on this resource'}, 403
    user['id'] = user.key.id

    if user['role'] == 'instructor':
        query = client.query(kind=COURSES)
        query.add_filter('instructor_id', '=', user['id'])
        courses = list(query.fetch())
        user['courses'] = []
        for c in courses:
            user['courses'].append(f'{request.url_root}{COURSES}/{c.key.id}')

    if user.get('avatar_file_name'):
        del user['avatar_file_name']

    return user

@app.route('/' + COURSES + '/<int:course_id>/students', methods=["PATCH"])
def update_enrollment(course_id):
    content = request.get_json()
    payload = verify_jwt(request, False)
    user_query = client.query(kind=USERS)
    if payload:
        user_query.add_filter(filter=PropertyFilter('sub', '=', payload['sub']))
        user_filter = query.Or([
            query.PropertyFilter('role', '=', 'admin'),
            query.PropertyFilter('role', '=', 'instructor')
        ])
        user_query.add_filter(filter=user_filter)
    else:
        return {'Error': 'Unauthorized'}, 401
    
    user = list(user_query.fetch())
    course_key = client.key(COURSES, course_id)
    course = client.get(key=course_key)

    if not user or (user[0].get('role') == 'instructor' and user[0].key.id != course['instructor_id']):
        return {'Error': 'You don\'t have permission on this resource'}, 403

    if not course:
        return {'Error': 'You don\'t have permission on this resource'}, 403
    
    if not course.get('enrollment'):
        course['enrollment'] = []
    
    for s in content['add']:
        if s in content['remove']:
            return {'Error': 'Enrollment data is invalid'}, 409
        #### optimize this ####
        student_key = client.key(USERS, s)
        student = client.get(key=student_key)
        if not student:
            return {'Error': 'Enrollment data is invalid'}, 409
        if s in course['enrollment']:
            continue
        course['enrollment'].append(s)

    for s in content['remove']:
        #### optimize this ####
        student_key = client.key(USERS, s)
        student = client.get(key=student_key)
        if not student:
            return {'Error': 'Enrollment data is invalid'}, 409
        if s not in course['enrollment']:
            continue
        course['enrollment'].remove(s)

    course.update({
        'enrollment': course['enrollment']
    })

    client.put(course)

    return '', 200

@app.route('/' + COURSES + '/<int:course_id>/students')
def get_enrollment(course_id):
    payload = verify_jwt(request, False)
    user_query = client.query(kind=USERS)
    if payload:
        user_query.add_filter(filter=PropertyFilter('sub', '=', payload['sub']))
        user_filter = query.Or([
            query.PropertyFilter('role', '=', 'admin'),
            query.PropertyFilter('role', '=', 'instructor')
        ])
        user_query.add_filter(filter=user_filter)
    else:
        return {'Error': 'Unauthorized'}, 401
    
    user = list(user_query.fetch())
    course_key = client.key(COURSES, course_id)
    course = client.get(key=course_key)

    if not user or (user[0].get('role') == 'instructor' and user[0].key.id != course['instructor_id']):
        return {'Error': 'You don\'t have permission on this resource'}, 403

    if not course:
        return {'Error': 'You don\'t have permission on this resource'}, 403
    

    return course['enrollment'], 200

@app.route('/' + USERS + '/<int:user_id>/avatar', methods=['POST'])
def ceate_avatar(user_id):
    payload = verify_jwt(request, False)
    if not payload:
        return {'Error': 'Unauthorized'}, 401
    
    user_key = client.key(USERS, user_id)
    user = client.get(key=user_key)
    if payload['sub'] != user['sub']:
        return {'Error': 'You don\'t have permission on this resource'}, 403

    if 'file' not in request.files:
        return {'Error': 'The request body is invalid'}, 400

    file_obj = request.files['file']

    storage_client = storage.Client()

    bucket = storage_client.get_bucket(PHOTO_BUCKET)

    file_name = file_obj.filename
    blob = bucket.blob(file_name)
    file_obj.seek(0)

    blob.upload_from_file(file_obj)

    user.update({
        'role': user['role'],
        'sub': user['sub'],
        'avatar_url': f'{request.url_root}{USERS}/{user.key.id}/avatar',
        'avatar_file_name': file_name   
    })

    client.put(user)

    return {'avatar_url': user['avatar_url']}


@app.route('/' + USERS + '/<int:user_id>/avatar')
def get_avatar(user_id):
    payload = verify_jwt(request, False)
    if not payload:
        return {'Error': 'Unauthorized'}, 401
    
    user_key = client.key(USERS, user_id)
    user = client.get(key=user_key)
    if not user:
        return {'Error': 'You don\'t have permission on this resource'}, 403
    if not user.get('avatar_url'):
        return {'Error': 'Not found'}, 404
    storage_client = storage.Client()

    bucket = storage_client.get_bucket(PHOTO_BUCKET)
    blob = bucket.blob(user['avatar_file_name'])

    file_obj = io.BytesIO()

    blob.download_to_file(file_obj)

    file_obj.seek(0)

    return send_file(file_obj, mimetype='image/x-png', download_name=user['avatar_file_name'])

@app.route('/' + USERS + '/<int:user_id>/avatar', methods=['DELETE'])
def delete_avatar(user_id):
    def delete_image(file_name):
        storage_client = storage.Client()
        bucket = storage_client.get_bucket(PHOTO_BUCKET)
        blob = bucket.blob(file_name)
        blob.delete()
        return 
    payload = verify_jwt(request, False)
    if not payload:
        return {'Error': 'Unauthorized'}, 401
    
    user_key = client.key(USERS, user_id)
    user = client.get(key=user_key)
    if not user or payload['sub'] != user['sub']:
        return {'Error': 'You don\'t have permission on this resource'}, 403

    if not user.get('avatar_url'):
        return {'Error': 'Not found'}, 404
    
    delete_image(user['avatar_file_name'])

    del user['avatar_url']
    del user['avatar_file_name']

    client.put(user)

    return '', 204
    
@app.route('/' + COURSES, methods=['POST'])
def create_course():
    payload = verify_jwt(request, False)
    #jwt belongs to an admin
    query = client.query(kind=USERS)
    if payload:
        query.add_filter('sub', '=', payload['sub'])
        query.add_filter('role', '=', 'admin')
    else:
        return {'Error': 'Unauthorized'}, 401
    
    admin = list(query.fetch())
    if not admin:
        return {'Error': 'You don\'t have permission on this resource'}, 403

    content = request.get_json()
    keys = ['subject', 'number', 'title', 'term', 'instructor_id']
    for k in keys:
        if not content.get(k):
            return {"Error": "The request body is invalid"}, 400


    instructor_key = client.key(USERS, content['instructor_id'])
    instructor = client.get(key=instructor_key)
    
    if not instructor or instructor['role'] != 'instructor':
        return {"Error": "The request body is invalid"}, 400
    
    new_key = client.key(COURSES)
    new_course = datastore.Entity(key=new_key)

    new_course.update({
        'instructor_id': content['instructor_id'],
        'number': content['number'],
        'subject': content['subject'],
        'term': content['term'],
        'title': content['title']
    })

    client.put(new_course)
    new_course['id'] = new_course.key.id
    new_course['self'] = f'{request.url_root}{COURSES}/{new_course.key.id}'

    return new_course, 201

@app.route('/' + COURSES, methods=['GET'])
def get_courses():
    offset = request.args.get('offset')
    limit = request.args.get('limit')
    if (not offset and not limit):
        offset = 0
        limit = 3
    else:
        offset = int(offset)
        limit = int(limit)

    query = client.query(kind=COURSES)
    query.order = ['subject']
    query_iter = query.fetch(limit=limit, offset=offset)
    pages = query_iter.pages
    results = list(next(pages))
    for r in results:
        r['id'] = r.key.id
        r['self'] = f'{request.url_root}{COURSES}/{r.key.id}'

    return {
        'courses': results,
        'next': f'{request.url_root}{COURSES}?limit={limit}&offset={offset+3}'
    }

@app.route('/' + COURSES + '/<int:course_id>')
def get_course(course_id):
    
    course_key = client.key(COURSES, course_id)
    course = client.get(key=course_key)

    if not course:
        return {'Error': 'Not found'}, 404

    course['id'] = course.key.id
    course['self'] = f'{request.url_root}{COURSES}/{course.key.id}'
    return course

@app.route('/' + COURSES + '/<int:course_id>', methods=['PATCH'])
def update_course(course_id):
    payload = verify_jwt(request, False)
    #jwt belongs to an admin
    query = client.query(kind=USERS)
    if payload:
        query.add_filter('sub', '=', payload['sub'])
        query.add_filter('role', '=', 'admin')
    else:
        return {'Error': 'Unauthorized'}, 401
    
    admin = list(query.fetch())
    if not admin:
        return {'Error': 'You don\'t have permission on this resource'}, 403
    
    content = request.get_json()
    if content.get('instructor_id'):
        instructor_key = client.key(USERS, content['instructor_id'])
        instructor = client.get(key=instructor_key)
        
        if not instructor or instructor['role'] != 'instructor':
            return {"Error": "The request body is invalid"}, 400
    
    course_key = client.key(COURSES, course_id)
    course = client.get(key=course_key)

    if not course:
        return {'Error': 'You don\'t have permission on this resource'}, 403
    
    course.update({
        'instructor_id': content['instructor_id'] if content.get('instructor_id') else course['instructor_id'],
        'subject': content['subject'] if content.get('subject') else course['subject'],
        'number': content['number'] if content.get('number') else course['number'],
        'title': content['title'] if content.get('title') else course['title'],
        'term': content['term'] if content.get('term') else course['term'],
    })

    client.put(course)

    course['id'] = course.key.id
    course['self'] = f'{request.url_root}{COURSES}/{course.key.id}'

    return course, 200

@app.route('/' + COURSES + '/<int:course_id>', methods=['DELETE'])
def delete_course(course_id):
    payload = verify_jwt(request, False)
    #jwt belongs to an admin
    query = client.query(kind=USERS)
    if payload:
        query.add_filter('sub', '=', payload['sub'])
        query.add_filter('role', '=', 'admin')
    else:
        return {'Error': 'Unauthorized'}, 401
    
    admin = list(query.fetch())
    if not admin:
        return {'Error': 'You don\'t have permission on this resource'}, 403
    
    course_key = client.key(COURSES, course_id)
    course = client.get(key=course_key)

    if not course:
        return {'Error': 'You don\'t have permission on this resource'}, 403
    
    client.delete(course_key)
    return '', 204

@app.errorhandler(AuthError)
def handle_auth_error(ex):
    
    response = jsonify(ex.error)
    response.status_code = ex.status_code
    return response

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)