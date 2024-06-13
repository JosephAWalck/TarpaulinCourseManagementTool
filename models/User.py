class User:
    def __init__(self, id, role, sub, avatar_url=None, avatar_file_name=None):
        self._id = id
        self._avatar_url = avatar_url
        self._avatar_file_name = avatar_file_name
        self._role = role
        self._sub = sub

    def get_id(self):
        return self._id
    
    def set_id(self, id):
        self._id = id
        return

    def get_avatar_url(self):
        return self._avatar_url
    
    def set_avatar_url(self, avatar_url):
        self._avatar_url = avatar_url
    
    def get_avatar_file_name(self):
        return self._avatar_file_name
    
    def set_avatar_file_name(self, avatar_file_name):
        self._avatar_file_name = avatar_file_name
        return
    
    def get_role(self):
        return self._role
    
    def set_role(self, role):
        self.role = role

    def get_sub(self):
        return self._sub
    
    def set_sub(self, sub):
        self._sub = sub
        return
    
    def to_dict(self):
        res = {
            'id': self._id,
            'role': self._role,
            'sub': self._sub
        }
        if self._avatar_url:
            res['avatar_url'] = self._avatar_url
        return res