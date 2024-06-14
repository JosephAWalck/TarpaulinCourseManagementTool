from flask import request
from config import USERS, COURSES
from utils.verify_jwt import verify_jwt
from google.cloud import datastore
from google.cloud.datastore import query
from google.cloud.datastore.query import PropertyFilter
from models.courses_repository import CourseRepository
from models.users_repository import UserRepository
from models.Course import Course

client = datastore.Client()

def create_course():
    course_instance = CourseRepository()
    user_instance = UserRepository()
    payload = verify_jwt(request, False)
    # is admin
    
    if not payload:
        return {'Error': 'Unauthorized'}, 401
    elif not user_instance.is_admin(payload['sub']):
        return {'Error': 'You don\'t have permission on this resource'}, 403

    content = request.get_json()
    keys = ['subject', 'number', 'title', 'term', 'instructor_id']
    for k in keys:
        if not content.get(k):
            return {"Error": "The request body is invalid"}, 400

    instructor = user_instance.get_user_by_id(content['instructor_id'])
    
    if not instructor or instructor.get_role() != 'instructor':
        return {"Error": "The request body is invalid"}, 400
    
    course = {
        'subject': content['subject'],
        'number': content['number'],
        'title': content['title'],
        'term': content['term'],
        'instructor_id': content['instructor_id']
    }
    
    new_course = course_instance.create_course(course)
    new_course['self'] = f'{request.url_root}{COURSES}/{course['id']}'
    return new_course, 201

def get_courses():
    course_instance = CourseRepository()
    offset = request.args.get('offset')
    limit = request.args.get('limit')
    if (not offset and not limit):
        offset = 0
        limit = 3
    else:
        offset = int(offset)
        limit = int(limit)

    courses = course_instance.get_courses(offset, limit)
    for c in courses:
        c['self'] = f'{request.url_root}{COURSES}/{c.key.id}'
    return {
        'courses': courses,
        'next': f'{request.url_root}{COURSES}?limit={limit}&offset={offset+3}'
    }

def get_course(course_id):
    # course_key = client.key(COURSES, course_id)
    # course = client.get(key=course_key)
    course_instance = CourseRepository()
    course = course_instance.get_course(course_id)
    if not course:
        return {'Error': 'Not found'}, 404

    course_dict = course.to_dict()
    course_dict['self'] = f'{request.url_root}{COURSES}/{course.get_id()}'
    return course_dict

def update_course(course_id):
    user_instance = UserRepository()
    course_instance = CourseRepository()
    content = request.get_json()
    payload = verify_jwt(request, False)
    if not payload:
        return {'Error': 'Unauthorized'}, 401

    course = course_instance.get_course(course_id)

    if not course:
        return {'Error': 'You don\'t have permission on this resource'}, 403
    
    if not user_instance.is_admin(payload['sub']):
        return {'Error': 'You don\'t have permission on this resource'}, 403
    
    if content.get('instructor_id'):
        instructor = user_instance.is_instructor(content['instructor_id'])
        if not instructor:
            return {"Error": "The request body is invalid"}, 400
    
    updated_course = course_instance.update_course(course_id, content)
    res = updated_course.to_dict()
    res['self'] = f'{request.url_root}{COURSES}/{updated_course.get_id()}'

    return res, 200

def delete_course(course_id):
    user_instance = UserRepository()
    course_instance = CourseRepository()
    payload = verify_jwt(request, False)
    #jwt belongs to an admin
    # query = client.query(kind=USERS)
    # if payload:
    #     query.add_filter(filter=PropertyFilter('sub', '=', payload['sub']))
    #     query.add_filter(filter=PropertyFilter('role', '=', 'admin'))
    # else:
    #     return {'Error': 'Unauthorized'}, 401
    if not payload:
        return {'Error': 'Unauthorized'}, 401
    elif not user_instance.is_admin(payload['sub']):
        return {'Error': 'You don\'t have permission on this resource'}, 403
    
    # admin = list(query.fetch())
    # if not admin:
    #     return {'Error': 'You don\'t have permission on this resource'}, 403
    
    # course_key = client.key(COURSES, course_id)
    # course = client.get(key=course_key)
    res = course_instance.delete_course(course_id)
    if not res:
        return {'Error': 'You don\'t have permission on this resource'}, 403
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