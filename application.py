import os
import requests
import simplejson as json

from flask import Flask, flash, session, render_template, request, redirect, url_for, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
# from model import *

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def index():
    if 'username' in session:
        username = session['username']
        return render_template("search.html", username=username)
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop('username', None)
    session.pop('userid', None)
    return redirect(url_for('index'))

@app.route("/register", methods=["POST"])
def register():
    """Register a new user"""

    username = request.form.get("username")
    password = request.form.get("password")
    email = request.form.get("email")
    count = db.execute("SELECT count(*) FROM users WHERE username = :username OR email = :email",
            {"username":username, "email":email}).fetchone()
    if count[0]==0:
        db.execute("INSERT INTO users(username, email, password) VALUES (:username, :email, crypt(:password, gen_salt('bf')))",
        {"username":username, "email":email, "password":password})
        db.commit()
    else:
        flash('Username/email already exists.','error')
        return redirect(url_for('index'))
    flash('User successfully registered','success')
    return redirect(url_for('index'))

@app.route("/login", methods=["POST","GET"])
def login():
    """Logs the user in and opens home page"""

    username = request.form.get("username")
    password = request.form.get("password")
    userid = db.execute("SELECT id FROM users WHERE username = :username and password = crypt(:pass, password)",
    {"username":username, "pass":password}).fetchone()
    if userid == None:
        flash('Username/password is incorrect. Please try again.','error')
        return redirect(url_for('index'))
    session['userid'] = int(userid[0])
    session['username']=username
    return render_template("search.html", username=username)

@app.route("/searchresults", methods=["GET", "POST"])
def searchresults():
    """Displays search results"""

    if 'username' not in session:
        flash("User needs to be logged in","error")
        return redirect(url_for('index'))
    username = session['username']
    query = request.args.get("query")
    books = db.execute("""SELECT * FROM books WHERE upper(isbn) LIKE (:query) OR upper(title) LIKE (:query) OR upper(author) LIKE (:query) 
                    UNION SELECT * FROM books WHERE lower(isbn) LIKE (:query) OR lower(title) LIKE (:query) OR lower(author) LIKE (:query)
                    ORDER BY AUTHOR""",
                    {"query":"%"+query+"%"}).fetchall()
    if len(books) == 0:
        flash("No matches found.","error")
        return render_template("search.html", username=username)
    return render_template("searchresults.html", books = books, username=username)

@app.route("/books/<string:isbn>")
def books(isbn):
    """Displays details about book"""

    if 'username' not in session:
        flash("User needs to be logged in","error")
        return redirect(url_for('index'))

    userid = session['userid']
    username = session['username']
    book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn":isbn}).fetchone()
    if book == None:
        return "Book does not exist"

    reviews = db.execute("SELECT * FROM reviews WHERE isbn = :isbn", {"isbn":book.isbn}).fetchall()
    average = db.execute("SELECT ROUND(AVG(rating),1) FROM reviews WHERE isbn = :isbn", {"isbn":book.isbn}).fetchone()[0]
    res = requests.get("https://www.goodreads.com/book/review_counts.json",
                    params={"isbns":isbn, "key":"XCwQB0F1RHlrVNTFop6hIw"})
    if res.status_code !=200:
        data = None
    else:
        data = res.json()

    return render_template("book.html", book=book, reviews=reviews,average=average, username=username, data=data["books"][0])

@app.route("/submit_review", methods=["POST"])
def submit_review():
    """Inserts review for the user"""

    if 'username' not in session:
        flash("User needs to be logged in","error")
        return redirect(url_for('index'))

    userid = session['userid']
    username = session['username']
    isbn = request.form.get("isbn")
    user_review = request.form.get("user_review")
    user_rating = request.form.get("rating")
    print(isbn,userid,username,user_review)
    if user_review is not None:
        db.execute("INSERT INTO reviews VALUES(:isbn, :userid, :username, :user_review, :user_rating)",
                    {"isbn":isbn, "userid":userid, "username":username, "user_review": user_review, "user_rating":user_rating})
        db.commit()
    flash('Review posted successfully','success')
    return redirect(url_for("books",isbn=isbn))

@app.route("/api/<string:isbn>")
def api(isbn):
    """Handles API call to get details about the book"""

    #Check if book exists
    book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn":isbn}).fetchone()
    if book == None:
        return jsonify({"error":"Invalid ISBN number"}),404

    count,average = db.execute("SELECT COUNT(*), ROUND(AVG(rating),1) FROM reviews WHERE isbn = :isbn", {"isbn":isbn}).fetchone()
    return jsonify({
        "title": book.title,
        "author": book.author,
        "year": book.year,
        "isbn": isbn,
        "review_count": count,
        "average_score": average
    })

class DecimalEncoder(json.JSONEncoder):
    def _iterencode(self, o, markers=None):
        if isinstance(o, decimal.Decimal):
            # wanted a simple yield str(o) in the next line,
            # but that would mean a yield on the line with super(...),
            # which wouldn't work (see my comment below), so...
            return (str(o) for o in [o])
        return super(DecimalEncoder, self)._iterencode(o, markers)