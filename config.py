# config.py
class Config(object):
    SQLALCHEMY_DATABASE_URI = 'postgresql://admin:123456@localhost:5433/Footy_Tipping_Master'
    SQLALCHEMY_TRACK_MODIFICATIONS = False