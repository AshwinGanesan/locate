import operator
import os
from flask import Flask, flash, redirect, render_template, request, session
from flask_migrate import Migrate
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure app to use PostgreSQL database
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.config["SQLALCHEMY_DATABASE_URI"] = "postgres://ygptyhmliybvtq:abf67ebf32fcae2c0ac8925e026fd47c1df44294b9a21f5a1bcf18d97bdb1f6e@ec2-176-34-183-20.eu-west-1.compute.amazonaws.com:5432/de9hiv1bu4a0kt"
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Create classes for PostgreSQL database tables
class User(db.Model):
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    username = db.Column(db.String(1024), nullable=False)
    pwd_hash = db.Column(db.String(1024), nullable=False)

    def __init__(self, username, pwd_hash):
        self.username = username
        self.pwd_hash = pwd_hash

class Score(db.Model):
    score_id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    score = db.Column(db.String(1024), nullable=False)

    def __init__(self, user_id, score):
        self.user_id = user_id
        self.score = score


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


@app.route("/")
def index():
    """Display home page"""

    return render_template("index.html")


@app.route("/changepwd", methods=["GET", "POST"])
@login_required
def changepwd():
    """Change password for user"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Query database for username
        row = User.query.filter_by(user_id=session["user_id"]).first()

        # Check if current password is correct
        if not check_password_hash(row.pwd_hash, request.form.get("current-password")):
            return apology("Incorrect password")

        # Check if new passwords match
        elif not request.form.get("new-password") == request.form.get("confirmation"):
            return apology("Passwords do not match")

        # Update password in database
        else:
            row.pwd_hash = generate_password_hash(request.form.get("new-password"))
            db.session.commit()

        # Redirect user to home page
            return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("changepwd.html")


@app.route("/leaderboard")
def leaderboard():
    """Display leaderboard"""

    # Query database for list of scores
    rows = Score.query.order_by(Score.score).all()

    # Replace user ids with usernames
    for entry in rows:
        rowInner = User.query.filter_by(user_id=entry.user_id).first()
        entry.username = rowInner.username

    # Sort list in ascending order

    return render_template("leaderboard.html", rows=rows)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.pop("user_id", None)

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("Username missing")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("Password missing")

        # Query database for username
        row = User.query.filter_by(username=request.form.get("username")).first()

        # Ensure username exists and password is correct
        if row == None or not check_password_hash(row.pwd_hash, request.form.get("password")):
            return apology("Invalid username or password")

        # Remember which user has logged in
        session["user_id"] = row.user_id
        session["logged_in"] = True

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.pop("user_id", None)

    # Redirect user to login form
    return redirect("/")

@app.route("/logscore", methods=["GET"])

def logscore():
    """Log user's score to SQL scores table"""

    # Add score to scores list if user is logged in
    if session.get("user_id") is not None:
        new_score = Score(session["user_id"], request.args.get("score"))
        db.session.add(new_score)
        db.session.commit()
    return ("", 204)


@app.route("/play")
def play():
    """Play game"""

    return render_template("play.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("Username missing")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("Password missing")

        # Check if passwords match
        elif not request.form.get("password") == request.form.get("confirmation"):
            return apology("Passwords do not match")

        # Check if username is already taken
        elif User.query.filter_by(username=request.form.get("username")).first() is not None:
            return apology("Username already taken")

        else:
            # Add user to database
            new_user = User(request.form.get("username"), generate_password_hash(request.form.get("password")))
            db.session.add(new_user)
            db.session.commit()

            # Remember which user has logged in
            session["user_id"] = new_user.user_id

            # Redirect user to home page
            return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/stats")
@login_required
def stats():
    """Display user stats"""

    # Default values for stats
    highScore = 50000
    rank = 0
    gamesPlayed = 0
    totalScore = 0

    # Query database for list of scores of logged in user
    rows = Score.query.filter_by(user_id=session["user_id"]).all()
    # Query database for list of all scores
    rowsAll = Score.query.order_by(Score.score).all()

    # Default value for average score
    if len(rows) == 0:
        avgScore = 0

    else:

        # Calculate high score, games played and average score
        for entry in rows:
            if float(entry.score) < highScore:
                highScore = float(entry.score)
            gamesPlayed += 1
            totalScore += float(entry.score)
        avgScore = str(round(totalScore / gamesPlayed, 2))

        # Calculate rank
        for entry in rowsAll:
            rank +=1
            if entry.user_id == session["user_id"]:
                break

    # Query database for username
    rowUser = User.query.filter_by(user_id=session["user_id"]).first()

    return render_template("stats.html", username=rowUser.username, highscore=highScore, rank=rank, gamesplayed=gamesPlayed, avgscore=avgScore)


def apology(message):
    """Render message as an apology to user."""
    return render_template("error.html", error=message)


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
