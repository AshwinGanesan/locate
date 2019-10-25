import operator
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps

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

# Configure CS50 Library to use SQLite database
db = SQL("postgres://ygptyhmliybvtq:abf67ebf32fcae2c0ac8925e026fd47c1df44294b9a21f5a1bcf18d97bdb1f6e@ec2-176-34-183-20.eu-west-1.compute.amazonaws.com:5432/de9hiv1bu4a0kt")


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
        rows = db.execute("SELECT * FROM users WHERE user_id = :user_id",
                          user_id=session["user_id"])

        # Check if current password is correct
        if not check_password_hash(rows[0]["hash"], request.form.get("current-password")):
            return apology("Incorrect password")

        # Check if new passwords match
        elif not request.form.get("new-password") == request.form.get("confirmation"):
            return apology("Passwords do not match")

        # Update password in database
        else:
            db.execute("UPDATE users SET hash = :password WHERE user_id = :user_id",
                       user_id=session["user_id"], password=generate_password_hash(request.form.get("new-password")))

        # Redirect user to home page
            return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("changepwd.html")


@app.route("/leaderboard")
def leaderboard():
    """Display leaderboard"""

    # Query database for list of scores
    rows = db.execute("SELECT user_id, score FROM scores")

    # Replace user ids with usernames
    for entry in rows:
        rowsInner = db.execute("SELECT username FROM users WHERE user_id = :user_id", user_id=entry["user_id"])
        entry["username"] = rowsInner[0]["username"]

    # Sort list in ascending order
    rowsSorted = sorted(rows, key=operator.itemgetter("score"))

    return render_template("leaderboard.html", rows=rowsSorted)


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
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("Invalid username or password")

        # Remember which user has logged in
        session["user_id"] = rows[0]["user_id"]
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
        db.execute("INSERT INTO scores (user_id, score) VALUES (:user_id, :score)", user_id=session["user_id"], score=request.args.get("score"))
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
        elif len(db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))) == 1:
            return apology("Username already taken")

        else:
            # Add user to database
            user_id = db.execute("INSERT INTO users (username, hash) VALUES (:username, :password)",
                                 username=request.form.get("username"), password=generate_password_hash(request.form.get("password")))

            # Remember which user has logged in
            session["user_id"] = user_id

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
    rows = db.execute("SELECT user_id, score FROM scores WHERE user_id = :user_id", user_id=session["user_id"])

    # Query database for list of all scores
    rowsAll = db.execute("SELECT user_id, score FROM scores")

    # Default value for average score
    if len(rows) == 0:
        avgScore = 0

    else:

        # Calculate high score, games played and average score
        for entry in rows:
            if float(entry["score"]) < highScore:
                highScore = float(entry["score"])
            gamesPlayed += 1
            totalScore += float(entry["score"])
        avgScore = str(round(totalScore / gamesPlayed, 2))

        # Calculate rank
        rowsAllSorted = sorted(rowsAll, key=operator.itemgetter("score"))
        for entry in rowsAllSorted:
            rank +=1
            if entry["user_id"] == session["user_id"]:
                break

    # Query database for username
    rowsUser = db.execute("SELECT username FROM users WHERE user_id = :user_id", user_id=session["user_id"])

    return render_template("stats.html", username=rowsUser[0]["username"], highscore=highScore, rank=rank, gamesplayed=gamesPlayed, avgscore=avgScore)


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
