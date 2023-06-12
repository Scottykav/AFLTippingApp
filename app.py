import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from flask import Flask, jsonify, render_template, request, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float
from config import Config
from werkzeug.security import check_password_hash, generate_password_hash
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY')
app.config.from_object(Config)
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@app.context_processor
def inject_user():
    return dict(user=current_user)

@app.route('/check_display_name')
def check_display_name():
    display_name = request.args.get('display_name')
    existing_user = User.query.filter_by(display_name=display_name).first()
    return {'exists': existing_user is not None}

@app.route('/check_email')
def check_email():
    email = request.args.get('email')
    existing_user = User.query.filter_by(email=email).first()
    return {'exists': existing_user is not None}

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            # User is logged in successfully!
            login_user(user)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('get_games'))
        else:
            flash('Invalid email or password.', 'error')
            return redirect(url_for('login'))

    return render_template('index.html')

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.first_name = request.form.get('first_name')
        current_user.last_name = request.form.get('last_name')
        current_user.mobile_number = request.form.get('mobile_number')
        db.session.commit()
        flash('Your profile has been updated.', 'success')
        return redirect(url_for('profile'))
    else:
        return render_template('profile.html')

from flask_login import UserMixin

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    display_name = Column(String(255), unique=True, nullable=False)
    first_name = Column(String(255))
    last_name = Column(String(255))
    mobile_number = Column(String(20))
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    registration_date = Column(DateTime, nullable=False, server_default=db.func.current_timestamp())
    last_login_date = Column(DateTime)
    is_admin = Column(Boolean, nullable=False, default=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Tip(db.Model):
    __tablename__ = 'tips'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    game_id = Column(Integer, nullable=False)
    selected_team = Column(String(255), nullable=False)
    confidence_score = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=db.func.current_timestamp())
    winning_team = Column(String(255), nullable=True)
    round_number = Column(Integer, nullable=False)

class Game(db.Model):
    __tablename__ = 'games'
    game_id = Column(Integer, primary_key=True)
    round_number = Column(Integer, nullable=False)
    date = Column(Float, nullable=False)
    location = Column(String(255), nullable=False)
    home_team = Column(String(255), nullable=False)
    away_team = Column(String(255), nullable=False)

@app.context_processor
def inject_user():
    return dict(user=current_user)

@app.before_request
def create_tables():
    # Now create all tables
    db.create_all()

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        display_name = request.form.get('display_name')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        mobile_number = request.form.get('mobile_number')
        email = request.form.get('email')
        password = generate_password_hash(request.form.get('password'))  # Hash the password

        # Check if display name already exists
        existing_user = User.query.filter_by(display_name=display_name).first()
        if existing_user:
            flash('This Display Name is already in use, please select another name.', 'error')
            return redirect(url_for('register'))

        # Check if email already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('This email is already in use. Please login with your existing registered email.', 'error')
            return redirect(url_for('register'))

        new_user = User(display_name=display_name, first_name=first_name, last_name=last_name, mobile_number=mobile_number, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()

        flash('Your account has been successfully created, you will now be redirected to <a href="/login">login</a>.', 'success')
    return render_template('register.html')   

def load_games():
    # Load the data
    games = Game.query.all()

    # Convert the SQLAlchemy result to a pandas DataFrame
    df = pd.DataFrame([{
        'game_id': game.game_id,
        'round_number': game.round_number,
        'date': game.date,
        'location': game.location,
        'home_team': game.home_team,
        'away_team': game.away_team,
    } for game in games])

    # Convert Excel date and time format to datetime
    def excel_date_to_datetime(excel_date):
        return pd.to_datetime('1899-12-30') + pd.to_timedelta(excel_date, unit='D')

    df['DateTime'] = df['date'].apply(excel_date_to_datetime)

    # Split the 'DateTime' column into 'Date' and 'Time' columns
    df['Time'] = df['DateTime'].dt.strftime('%I:%M %p')
    df['date'] = df['DateTime'].dt.strftime('%A %d %b %Y')

    # Replace spaces in column names with underscores
    df.columns = df.columns.str.replace(' ', '_')

    # Define a dictionary that maps team names to their logo paths
    team_logos = {
        'North Melbourne': 'team_logos/North_Melbourne_Kangaroos_logo_NMFC.png',
        'Sydney Swans': 'team_logos/Sydney_Swans_logo_logotype.png',
        'Geelong Cats': 'team_logos/Geelong_Cats_logo.png',
        'GWS Giants': 'team_logos/GWS_Giants_logo_Greater_Western-Sydney_Giants.png',
        'Adelaide Crows': 'team_logos/Adelaide_Crows_logo_logotype_emblem.png',
        'Hawthorn': 'team_logos/Hawthorn_Hawks_logo.png',
        'West Coast Eagles': 'team_logos/West_Coast_Eagles_logo_logotype.png',
        'Western Bulldogs': 'team_logos/Western_Bulldogs_logo_logotype.png',
        'Port Adelaide': 'team_logos/Port_Adelaide_Power_logo_black.png',
        'Carlton': 'team_logos/Carlton_Blues_logo.png',
        'Melbourne': 'team_logos/Melbourne_Demons_logo_logotype.png',
        'Collingwood': 'team_logos/Collingwood_Magpies_logo.png',
        'Richmond': 'team_logos/Richmond_Tigers_logo_transparent_bg.png',
        'Gold Coast Suns': 'team_logos/Gold_Coast_Suns_logo-700x571.png',
        'St Kilda': 'team_logos/St_Kilda_Saints_logo.png',
        'Brisbane Lions': 'team_logos/Brisbane_Lions_logo.png',
        'Fremantle': 'team_logos/Fremantle_Dockers_logo.png',
        'Essendon': 'team_logos/Essendon_Bombers_logo.png',
    }

    # Add the paths to the team logos
    df['home_team_Logo'] = df['home_team'].map(team_logos)
    df['away_team_Logo'] = df['away_team'].map(team_logos)

    # Get today's date
    today = datetime.now()

    # Group the data by round number and get the max date for each round
    round_dates = df.groupby('round_number')['DateTime'].max()

    # Find the current round number
    current_round = round_dates[round_dates >= today].idxmin()

    # Filter the data to only include games from the current round
    current_games = df[df['round_number'] == current_round]

    # Create a list of rounds
    rounds = df['round_number'].unique().tolist()

    # Sort the rounds in ascending order
    rounds.sort()

    return df, rounds

@app.route('/games', methods=['GET'])
@login_required
def get_games():
    games, rounds = load_games()  # Get the games and rounds
    games_dict = games.to_dict(orient='records')

    # Convert numpy types to native Python types
    for game in games_dict:
        for key, value in game.items():
            if isinstance(value, np.integer):
                game[key] = int(value)
            elif isinstance(value, np.floating):
                game[key] = float(value)
            elif isinstance(value, np.bool_):
                game[key] = bool(value)

    # Render the games.html template and pass the games data and rounds to it
    return render_template('games.html', games=games_dict, rounds=rounds, tips=tips)

@app.route('/submit_tips', methods=['POST'])
@login_required
def submit_tips():
    tips = request.get_json()

    for gameId, tip in tips.items():
        game = Game.query.get(gameId)

        # Try to fetch an existing tip
        existing_tip = Tip.query.filter_by(user_id=current_user.id, game_id=gameId).first()

        if existing_tip:
            # If a tip exists, update it
            existing_tip.selected_team = tip['selectedTeam']
            existing_tip.confidence_score = tip['confidenceScore']
        else:
            # If no tip exists, create a new one
            new_tip = Tip(user_id=current_user.id, game_id=gameId, selected_team=tip['selectedTeam'], confidence_score=tip['confidenceScore'], round_number=game.round_number)
            db.session.add(new_tip)

    db.session.commit()

    return '', 200  # Return a success status

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
