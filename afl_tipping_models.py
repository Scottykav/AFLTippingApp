from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)

class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    round = db.Column(db.String(50))
    date = db.Column(db.DateTime)  # Changed from db.String(50) to db.DateTime
    home_team = db.Column(db.String(50))
    away_team = db.Column(db.String(50))
    location = db.Column(db.String(50))  # Changed 'Location' to 'location'


class Tip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'), nullable=False)
    tipped_team = db.Column(db.String(50), nullable=False)
    confidence = db.Column(db.Integer, nullable=False)
