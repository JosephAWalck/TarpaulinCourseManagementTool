from flask import request
from config import USERS, COURSES
from utils.verify_jwt import verify_jwt
from google.cloud import datastore
from models.courses_repository import CourseRepository
from models.users_repository import UserRepository

client = datastore.Client()

def create_course():
    course_instance = CourseRepository()
    user_instance = UserRepository()
    payload = verify_jwt(request, False)

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

    if not payload:
        return {'Error': 'Unauthorized'}, 401
    elif not user_instance.is_admin(payload['sub']):
        return {'Error': 'You don\'t have permission on this resource'}, 403
    
    res = course_instance.delete_course(course_id)
    if not res:
        return {'Error': 'You don\'t have permission on this resource'}, 403
    return '', 204

def update_enrollment(course_id):
    user_instance = UserRepository()
    course_instance = CourseRepository()
    content = request.get_json()
    payload = verify_jwt(request, False)
    if not payload:
        return {'Error': 'Unauthorized'}, 401
    user = user_instance.get_admin_instructor(payload['sub'])
    course = course_instance.get_course(course_id)

    if not user or not course or (user.get_role() == 'instructor' and user.get_id() != course.get_instructor_id()):
        return {'Error': 'You don\'t have permission on this resource'}, 403
    
    if course.get_enrollment():
        enrollment = course.get_enrollment()
    else:
        enrollment = []

    add_students = user_instance.get_user_list(content['add'])
    remove_students = user_instance.get_user_list(content['remove'])

    if add_students is None or remove_students is None:
        return {'Error': 'Enrollment data is invalid'}, 409
    
    result = course_instance.update_enrollment(course.get_id(), add_students, remove_students, enrollment)
    if not result:
        return {'Error': 'Enrollment data is invalid'}, 409

    return '', 200

def get_enrollment(course_id):
    user_instance = UserRepository()
    course_instance = CourseRepository()
    payload = verify_jwt(request, False)
    if not payload:
        return {'Error': 'Unauthorized'}, 401
    user = user_instance.get_admin_instructor(payload['sub'])

    course = course_instance.get_course(course_id)
    if not user or not course or (user.get_role() == 'instructor' and user.get_id() != course.get_instructor_id()):
        return {'Error': 'You don\'t have permission on this resource'}, 403

    if course.get_enrollment():
        return course.get_enrollment(), 200
    return [], 200
    