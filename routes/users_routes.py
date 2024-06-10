from flask import Blueprint
from controllers.users_controllers import get_all_users, get_user, create_avatar, get_avatar, delete_avatar, login_user

user_blueprint = Blueprint('user_blueprint', __name__)

user_blueprint.route('/', methods=['GET'])(get_all_users)
user_blueprint.route('/login', methods=['POST'])(login_user)
user_blueprint.route('/<int:user_id>', methods=['GET'])(get_user)
user_blueprint.route('/<int:user_id>/avatar', methods=['POST'])(create_avatar)
user_blueprint.route('/<int:user_id>/avatar', methods=['GET'])(get_avatar)
user_blueprint.route('/<int:user_id>/avatar', methods=['DELETE'])(delete_avatar)
