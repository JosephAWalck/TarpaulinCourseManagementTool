from google.cloud import datastore, storage
from google.cloud.datastore.query import PropertyFilter
from config import USERS, PHOTO_BUCKET
from models.User import User
import io

class UserRepository:
    def __init__(self):
        self._client = datastore.Client()
        self._storage_client = storage.Client()

    def is_admin(self, sub):
        query = self._client.query(kind=USERS)
        query.add_filter(filter=PropertyFilter('sub', '=', sub))
        query.add_filter(filter=PropertyFilter('role', '=', 'admin'))
        res = list(query.fetch())
        if not res:
            return False
        return True
    
    def is_instructor(self, instructor_id):
        instructor_key = self._client.key(USERS, instructor_id)
        instructor = self._client.get(key=instructor_key)

        if not instructor or instructor['role'] != 'instructor':
            return None
        return instructor
 
    def get_users(self):
        query = self._client.query(kind=USERS)
        users = list(query.fetch())
        result = []
        for u in users:
            user_obj = User(u.key.id, u['role'], u['sub'])
            result.append(user_obj.to_dict())
        return result
    
    def get_user_by_sub(self, sub):
        query = self._client.query(kind=USERS)
        query.add_filter(filter=PropertyFilter('sub', '=', sub))
        res = list(query.fetch())
        if not res:
            return None
        return User(res[0].key.id, 
                    res[0]['role'], 
                    res[0]['sub'],
                    res[0].get('avatar_url'),
                    res[0].get('avatar_file_name'))
        
    
    def get_user_by_id(self, id):
        user_key = self._client.key(USERS, id)
        user = self._client.get(key=user_key)
        if not user:
            return None
        return User(user.key.id, 
            user['role'], 
            user['sub'], 
            user.get('avatar_url'), 
            user.get('avatar_file_name'))

    def create_avatar(self, file_object, user_obj, file_url):
        bucket = self._storage_client.get_bucket(PHOTO_BUCKET)
        user_key = self._client.key(USERS, user_obj.get_id())
        user = self._client.get(key=user_key)

        file_name = file_object.filename
        blob = bucket.blob(file_name)
        file_object.seek(0)

        blob.upload_from_file(file_object)

        user.update({
            'role': user_obj.get_role(),
            'sub': user_obj.get_sub(),
            'avatar_url': file_url,
            'avatar_file_name': file_name
        })
        
        self._client.put(user)
        user_obj.set_avatar_url(file_url)
        user_obj.set_avatar_file_name(file_name)
        return
    
    def get_avatar(self, avatar_file_name):
        bucket = self._storage_client.get_bucket(PHOTO_BUCKET)
        blob = bucket.blob(avatar_file_name)

        file_obj = io.BytesIO()

        blob.download_to_file(file_obj)

        file_obj.seek(0)

        return file_obj
    
    def delete_avatar(self, user_obj):
        bucket = self._storage_client.get_bucket(PHOTO_BUCKET)
        blob = bucket.blob(user_obj.get_avatar_file_name())
        blob.delete()

        user_key = self._client.key(USERS, user_obj.get_id())
        user = self._client.get(key=user_key)

        del user['avatar_url']
        del user['avatar_file_name']

        self._client.put(user)

        return
