from flask import request, send_file
from config import USERS, COURSES, PHOTO_BUCKET, CLIENT_ID, CLIENT_SECRET, DOMAIN
from utils.verify_jwt import verify_jwt
from google.cloud import datastore, storage
from google.cloud.datastore import query
from google.cloud.datastore.query import PropertyFilter
from models.users_repository import UserRepository

import requests
import io

client = datastore.Client()

def get_all_users():
    user_instance = UserRepository()
    payload = verify_jwt(request, False)
    if not payload:
        return {'Error': 'Unauthorized'}, 401
    elif not user_instance.is_admin(payload['sub']):
        return {'Error': 'You don\'t have permission on this resource'}, 403
    
    res = user_instance.get_users()
    return res

def get_user(user_id):
    user_instance = UserRepository()
    payload = verify_jwt(request, False)
    if not payload:
        return {'Error': 'Unauthorized'}, 401
    req = user_instance.get_user_by_sub(payload['sub'])
    user = user_instance.get_user_by_id(user_id)
    res = user.to_dict()
    if not user:
        return {'Error': 'You don\'t have permission on this resource'}, 403
    elif payload['sub'] != user.get_sub() and req.get_role() != 'admin':
        return {'Error': 'You don\'t have permission on this resource'}, 403

    if user.get_role() == 'instructor':
        # Course model and repository
        query = client.query(kind=COURSES)
        query.add_filter(filter=PropertyFilter('instructor_id', '=', user.get_id()))
        courses = list(query.fetch())
        res['courses'] = []
        for c in courses:
            res['courses'].append(f'{request.url_root}{COURSES}/{c.key.id}')
    elif user.get_role() == 'student':
        #Course model and repository
        query = client.query(kind=COURSES)
        courses = list(query.fetch())
        res['courses'] = []
        for c in courses:
            if c.get('enrollment') and (user.get_id() in c['enrollment']):
                res['courses'].append(f'{request.url_root}{COURSES}/{c.key.id}')
    
    return res

def create_avatar(user_id):
    user_instance = UserRepository()
    if 'file' not in request.files:
        return {'Error': 'The request body is invalid'}, 400

    payload = verify_jwt(request, False)
    if not payload:
        return {'Error': 'Unauthorized'}, 401
    
    user = user_instance.get_user_by_id(user_id)
    if payload['sub'] != user.get_sub():
        return {'Error': 'You don\'t have permission on this resource'}, 403

    file_obj = request.files['file']
    file_url = f'{request.url_root}{USERS}/{user.get_id()}/avatar'
    user_instance.create_avatar(file_obj, user, file_url)

    return {'avatar_url': user.get_avatar_url()}, 200

def get_avatar(user_id):
    user_instance = UserRepository()
    payload = verify_jwt(request, False)
    if not payload:
        return {'Error': 'Unauthorized'}, 401
    
    user = user_instance.get_user_by_id(user_id)
    if user.get_sub() != payload['sub']:
        return {'Error': 'You don\'t have permission on this resource'}, 403
    if not user.get_avatar_url():
        return {'Error': 'Not found'}, 404
    
    file_obj = user_instance.get_avatar(user.get_avatar_file_name())
    return send_file(file_obj, mimetype='image/x-png', download_name=user.get_avatar_file_name())

def delete_avatar(user_id):
    user_instance = UserRepository() 
    payload = verify_jwt(request, False)
    if not payload:
        return {'Error': 'Unauthorized'}, 401
    
    user = user_instance.get_user_by_id(user_id)
    if not user or payload['sub'] != user.get_id():
        return {'Error': 'You don\'t have permission on this resource'}, 403

    if not user.get_avatar_url():
        return {'Error': 'Not found'}, 404
    
    user_instance.delete_avatar(user)

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