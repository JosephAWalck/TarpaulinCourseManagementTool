from flask import Blueprint
from controllers.courses_controllers import create_course, update_enrollment, get_enrollment, get_courses, get_course, update_course, delete_course

courses_blueprint = Blueprint('courses_blueprint', __name__)

courses_blueprint.route('/', methods=['POST'])(create_course)
courses_blueprint.route('/', methods=['GET'])(get_courses)
courses_blueprint.route('/<int:course_id>', methods=['GET'])(get_course)
courses_blueprint.route('/<int:course_id>', methods=['PATCH'])(update_course)
courses_blueprint.route('/<int:course_id>', methods=['DELETE'])(delete_course)
courses_blueprint.route('/<int:course_id>/students', methods=['PATCH'])(update_enrollment)
courses_blueprint.route('/<int:course_id>/students', methods=['GET'])(get_enrollment)