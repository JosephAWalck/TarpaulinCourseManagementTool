class Course:
    def __init__(self, 
                 id,
                 subject=None, 
                 number=None, 
                 title=None, 
                 term=None, 
                 instructor_id=None):
        self._id = id
        self._subject = subject
        self._number = number
        self._title = title
        self._term = term
        self._instructor_id = instructor_id

    def get_id(self):
        return self._id

    def set_id(self, id):
        self._id = id

    def get_subject(self):
        return self._subject
    
    def set_subject(self, subject):
        self._subject = subject
        return
    
    def get_number(self):
        return self._subject
    
    def set_number(self, number):
        self._number = number
        return

    def get_title(self):
        return self._title
    
    def set_title(self, title):
        self._title = title
        return
    
    def get_term(self):
        return self._term
    
    def set_term(self, term):
        self._term = term
        return
    
    def get_instructor_id(self):
        return self._instructor_id
    
    def set_instructor_id(self, instructor_id):
        self._instructor_id = instructor_id
        return
    
    def to_dict(self):
        return {
            'id': self._id,
            'subject': self._subject,
            'number': self._number,
            'title': self._title,
            'term': self._term,
            'instructor_id': self._instructor_id
        }