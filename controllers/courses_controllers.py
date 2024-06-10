from flask import request
from config import USERS, COURSES
from utils.verify_jwt import verify_jwt
from google.cloud import datastore
from google.cloud.datastore import query
from google.cloud.datastore.query import PropertyFilter

client = datastore.Client()

def create_course():
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

def get_course(course_id):
    course_key = client.key(COURSES, course_id)
    course = client.get(key=course_key)

    if not course:
        return {'Error': 'Not found'}, 404

    course['id'] = course.key.id
    course['self'] = f'{request.url_root}{COURSES}/{course.key.id}'
    return course

def update_course(course_id):
    content = request.get_json()
    payload = verify_jwt(request, False)
    #jwt belongs to an admin
    query = client.query(kind=USERS)
    if payload:
        query.add_filter(filter=PropertyFilter('sub', '=', payload['sub']))
        query.add_filter(filter=PropertyFilter('role', '=', 'admin'))
    else:
        return {'Error': 'Unauthorized'}, 401
    
    course_key = client.key(COURSES, course_id)
    course = client.get(key=course_key)

    if not course:
        return {'Error': 'You don\'t have permission on this resource'}, 403
    
    admin = list(query.fetch())
    if not admin:
        return {'Error': 'You don\'t have permission on this resource'}, 403
    
    
    if content.get('instructor_id'):
        instructor_key = client.key(USERS, content['instructor_id'])
        instructor = client.get(key=instructor_key)
        
        if not instructor or instructor['role'] != 'instructor':
            return {"Error": "The request body is invalid"}, 400
    
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

def delete_course(course_id):
    payload = verify_jwt(request, False)
    #jwt belongs to an admin
    query = client.query(kind=USERS)
    if payload:
        query.add_filter(filter=PropertyFilter('sub', '=', payload['sub']))
        query.add_filter(filter=PropertyFilter('role', '=', 'admin'))
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
    
    if course.get('enrollment'):
        return course['enrollment'], 200
    else:
        return [], 200