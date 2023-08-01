from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
import random
import pandas as pd
import secrets
import imdb
from io import BytesIO
from jinja2 import Environment


app = Flask(__name__)
secret_key = secrets.token_hex(16)  # Generate a random 16-byte secret key

app.secret_key = 'secret_key'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'nandhu@1234567890'
app.config['MYSQL_DB'] = 'moviereclogin'
 
mysql = MySQL(app)
 
@app.route('/')
@app.route('/login', methods =['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT id, username, password FROM accounts WHERE username = %s AND password = %s', (username, password,))

        account = cursor.fetchone()
        if account:
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            msg = 'Logged in successfully !'
            return render_template('index.html', msg = msg)
        else:
            msg = 'Incorrect username / password !'
    return render_template('login.html', msg = msg)
 
@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return redirect(url_for('login'))
 
@app.route('/register', methods =['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form :
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = % s', (username, ))
        account = cursor.fetchone()
        if account:
            msg = 'Account already exists !'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address !'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers !'
        elif not username or not password or not email:
            msg = 'Please fill out the form !'
        else:
            cursor.execute('INSERT INTO accounts VALUES (NULL, % s, % s, % s)', (username, password, email, ))
            mysql.connection.commit()
            msg = 'You have successfully registered !'
    elif request.method == 'POST':
        msg = 'Please fill out the form !'
    return render_template('register.html', msg = msg)

# Load the dataset containing film titles
df = pd.read_csv('output.csv')

@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/recommend', methods=['POST'])
def recommend():
    genre = request.form['genre']
    year_range = request.form['year_range']

    # Preprocess the user input, filter the dataset, and select movies
    recommended_films, recommended_films_details = make_recommendations(genre, year_range)

    # Pass the zip function to the template context
    env = Environment()
    env.globals.update(zip=zip)

    return render_template('recommend.html', films=recommended_films, film_details=recommended_films_details, zip=zip)



def make_recommendations(genre, year_range):
    # Convert year_range to integers
    start_year, end_year = map(int, year_range.split('-'))

    # Normalize genre input (remove leading/trailing whitespace and convert to lowercase)
    genre = genre.strip().lower()

    # Filter the dataset based on genre and year range
    filtered_df = df[(df['Genres'].str.lower().str.contains(genre)) & (df['Year'].between(start_year, end_year))]

    # Select movies with Your Rating > 8
    high_rated_films = filtered_df[filtered_df['Your Rating'] > 8]

    # Shuffle the movies randomly
    high_rated_films = high_rated_films.sample(frac=1)

    # Get the top 3 films
    top_films = high_rated_films.head(3)

    # Retrieve the actual film titles
    recommended_films = top_films['Title'].tolist()
    # Retrieve the actual film details
    ia = imdb.IMDb()
    recommended_films_details = []
    for film in recommended_films:
        movie_id = ia.search_movie(film)[0].movieID
        movie = ia.get_movie(movie_id)
        recommended_films_details.append(movie)


    return recommended_films, recommended_films_details

if __name__ == '__main__':
    app.run(debug=True,port=8000)
