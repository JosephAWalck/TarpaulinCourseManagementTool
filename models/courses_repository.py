from google.cloud import datastore
from models.Course import Course
from config import COURSES

class CourseRepository:
    def __init__(self):
        self._client = datastore.Client()

    def create_course(self, course):
        new_course_key = self._client.key(COURSES)
        new_course = datastore.Entity(key=new_course_key)

        new_course.update(course)

        self._client.put(new_course)
        course['id'] = new_course.key.id
        return course
    
    def get_courses(self, offset, limit):
        query = self._client.query(kind=COURSES)
        query.order = ['subject']
        query_iter = query.fetch(limit=limit, offset=offset)
        pages = query_iter.pages
        results = list(next(pages))
        for r in results:
            r['id'] = r.key.id

        return results

    def get_course(self, course_id):
        course_key = self._client.key(COURSES, course_id)
        course = self._client.get(key=course_key)
        if not course:
            return None
        return Course(course.key.id,
                course.get('subject'),
                course.get('number'),
                course.get('title'),
                course.get('term'),
                course.get('instructor_id'),
                course.get('enrollment'))
    
    def update_course(self, course_id, content):
        course_key = self._client.key(COURSES, course_id)
        course = self._client.get(key=course_key)

        course.update({
            'subject': content['subject'] if content.get('subject') else course['subject'],
            'number': content['number'] if content.get('number') else course['number'],
            'title': content['title'] if content.get('title') else course['title'],
            'term': content['term'] if content.get('term') else course['term'],
            'instructor_id': content['instructor_id'] if content.get('instructor_id') else course['instructor_id'],
        })

        self._client.put(course)
        return Course(course.key.id,
                      course['subject'],
                      course['number'],
                      course['title'],
                      course['term'],
                      course['instructor_id'])

    def delete_course(self, course_id):
        course_key = self._client.key(COURSES, course_id)
        course = self._client.get(key=course_key)

        if not course:
            return False
        
        self._client.delete(course_key)
        return True
    
    def update_enrollment(self, course_id, add, remove, enrollment):
        course_key = self._client.key(COURSES, course_id)
        course = self._client.get(key=course_key)
    
        for s in add:
            if s in remove:
                return None
            elif s in enrollment:
                continue
            enrollment.append(s)

        for s in remove:
            if s not in enrollment:
                continue
            enrollment.remove(s)

        course.update({
            'enrollment': enrollment
        })

        self._client.put(course)
        return Course(
            course.key.id,
            course['subject'],
            course['number'],
            course['title'],
            course['term'],
            course['instructor_id'],
            course['enrollment']
        )