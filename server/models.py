ROLE_USER = 0
ROLE_ADMIN = 1

class User():
    requests = False

    def __init__(self, email, username, idp ):
        self.email=email
        self.id = "-1"
        self.name = ""
        self.idp = idp
        self.role = ROLE_USER
        self.username = username


    def set_query_requests(self,requests):
        "set requests for all User class instances"
        self.requests = requests

    def set_global_query_requests(self,requests):
        "set requests for all User class instances"
        User.requests = requests

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

    def __repr__(self):
        return '<User %r>' % (self.username)
       
#    def as_dict(self):
#        return {c.name: getattr(self, c.name) for c in self.__table__.columns} 

