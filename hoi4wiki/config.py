import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'zovovozTainiyKlyuch'
    WTF_CSRF_SECRET_KEY = 'zovovozTainiyKlyuch'
    SQLALCHEMYDATABASEURI = os.environ.get('DATABASEURL') or 'sqlite:///hoi4wiki.db'
    SQLALCHEMYTRACKMODIFICATIONS = False