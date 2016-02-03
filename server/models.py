from flask.ext.login import UserMixin
ROLE_GUEST = 0
ROLE_USER = 1
ROLE_ADMIN = 100


class UserNotFoundError(Exception):
    print('Error, user not found',str(Exception))
    pass


class User(UserMixin):
    "User class for use by flask login. Abstracts away underlying databases."
    #user_database may be replaced by an actual database in __init__
    requests = False
    user_database = {"jcwright@mit.edu":{"email":"jcwright@mit.edu",
                        "username":"jcwright@mit.edu",
                        "role":ROLE_USER,
                        "name":"John C. Wright",
                        "password":"blank",
                        "auth_method":"password",
                        "idp":"MIT"
                          }}

    def __init__(self, id ):
        if not id in self.user_database:
            raise UserNotFoundError()
        rec=self.user_database[id]

        self.email=rec['email']
        self.id = id
        self.name = rec["name"]
        self.idp = rec['idp']
        self.role = rec['role']
        self.username = rec['username']
        self.password = rec['password']


    def set_query_requests(self,requests):
        "set requests for this User class instance"
        self.requests = requests


    @classmethod
    def set_global_query_requests(cls,requests):
        "set requests for all User class instances"
        cls.requests = requests

        
    def query(self,request):
        return User(self.requests.get(request).json())


    def add(self):
        return True


    def is_authenticated(self):
        return True

    
    def is_authorized(self):
        return True

    
    def is_active(self):
        return True

    
    def is_anonymous(self):
        return False

    
    def get_id(self):
        return unicode(self.id)

    
    @classmethod
    def get(cls,id):
        '''Return user instance of id, return None if not exist.'''
        try:
            return cls(id)
        except UserNotFoundError:
            return None

    
    def __repr__(self):
        return '<User %r>' % (self.username)

#    def as_dict(self):
#        return {c.name: getattr(self, c.name) for c in self.__table__.columns} 

