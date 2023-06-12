from flask import Flask, render_template
import pandas as pd
from datetime import datetime, timedelta

app = Flask(__name__)

def float_to_datetime(float_date):
    base_date = datetime(1899, 12, 30)
    delta = timedelta(days=float_date)
    return base_date + delta

@app.route('/games')
def display_games():
    games = pd.read_csv('/Users/scottkavanagh/Python/AFL Tipping App/afl-2023-UTC.csv')
    games['Date'] = games['Date'].apply(float_to_datetime)
    future_games = games[games['Date'] > datetime.now()]
    return render_template('games.html', games=future_games)

if __name__ == '__main__':
    app.run(debug=True)
