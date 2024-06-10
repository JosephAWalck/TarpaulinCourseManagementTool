from flask import request, send_file
from config import USERS, COURSES, PHOTO_BUCKET, CLIENT_ID, CLIENT_SECRET, DOMAIN
from utils.verify_jwt import verify_jwt
from google.cloud import datastore, storage
from google.cloud.datastore import query
from google.cloud.datastore.query import PropertyFilter

import requests
import io

client = datastore.Client()

def get_all_users():
    payload = verify_jwt(request, False)
    query = client.query(kind=USERS)
    if payload:
        query.add_filter(filter=PropertyFilter('sub', '=', payload['sub']))
        query.add_filter(filter=PropertyFilter('role', '=', 'admin'))
    else:
        return {'Error': 'Unauthorized'}, 401
    
    admin = list(query.fetch())
    if not admin:
        return {'Error': 'You don\'t have permission on this resource'}, 403
    query = client.query(kind=USERS)
    users = list(query.fetch())
    result = []
    for u in users:
        result.append({
            'id': u.key.id,
            'role': u['role'],
            'sub': u['sub']
        })
        
    return result

def get_user(user_id):
    payload = verify_jwt(request, False)
    if not payload:
        return {'Error': 'Unauthorized'}, 401
    jwt_query = client.query(kind=USERS)
    jwt_query.add_filter(filter=PropertyFilter('sub', '=', payload['sub']))
    jwt = list(jwt_query.fetch())

    user_key = client.key(USERS, user_id)
    user = client.get(key=user_key)
    
    if not user:
        return {'Error': 'You don\'t have permission on this resource'}, 403
    elif payload['sub'] != user['sub'] and jwt[0]['role'] != 'admin':
        return {'Error': 'You don\'t have permission on this resource'}, 403
    
    user['id'] = user.key.id

    if user['role'] == 'instructor':
        query = client.query(kind=COURSES)
        query.add_filter(filter=PropertyFilter('instructor_id', '=', user['id']))
        courses = list(query.fetch())
        user['courses'] = []
        for c in courses:
            user['courses'].append(f'{request.url_root}{COURSES}/{c.key.id}')
    elif user['role'] == 'student':
        query = client.query(kind=COURSES)
        courses = list(query.fetch())
        user['courses'] = []
        for c in courses:
            if c.get('enrollment') and (user.key.id in c['enrollment']):
                user['courses'].append(f'{request.url_root}{COURSES}/{c.key.id}')

    if user.get('avatar_file_name'):
        del user['avatar_file_name']

    return user

def create_avatar(user_id):
    if 'file' not in request.files:
        return {'Error': 'The request body is invalid'}, 400

    payload = verify_jwt(request, False)
    if not payload:
        return {'Error': 'Unauthorized'}, 401
    
    user_key = client.key(USERS, user_id)
    user = client.get(key=user_key)
    if payload['sub'] != user['sub']:
        return {'Error': 'You don\'t have permission on this resource'}, 403

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

    return {'avatar_url': user['avatar_url']}, 200

def get_avatar(user_id):
    payload = verify_jwt(request, False)
    if not payload:
        return {'Error': 'Unauthorized'}, 401
    
    user_key = client.key(USERS, user_id)
    user = client.get(key=user_key)
    if user['sub'] != payload['sub']:
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