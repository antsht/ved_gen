import os
import datetime

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd, weak_password

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    fundsavailable = db.execute(
        "SELECT cash FROM users where id = ?", session["user_id"]
    )[0]["cash"]
    purchases = db.execute(
        "SELECT symbol, SUM(amount*action) as amount FROM purchases where user_id = ? GROUP BY symbol",
        session["user_id"],
    )
    sum = 0
    for p in purchases:
        quote = lookup(p["symbol"])
        p["price"] = quote["price"]
        p["name"] = quote["name"]
        p["total"] = quote["price"] * p["amount"]
        sum += p["total"]
    return render_template(
        "index.html",
        purchases=purchases,
        cash=fundsavailable,
        total=sum + fundsavailable,
    )


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    if request.method == "GET":
        return render_template("buy.html")
    if request.method == "POST":
        try:
            symbol = request.form.get("symbol")
            if symbol is None or len(symbol) == 0:
                return apology("Enter symbol")
            quote = lookup(symbol)
            if quote == None:
                return apology("Not existing symbol")
            shares = request.form.get("shares")
            if shares == None or int(shares) < 1 or float(shares) != int(shares):
                return apology("Invalid share (must be > 0)")
        except ValueError:
            return apology("Invalid share (must be integer > 0)")
        fundsavailable = db.execute(
            "SELECT cash FROM users where id = ?", session["user_id"]
        )[0]["cash"]
        if fundsavailable < (quote["price"] * int(shares)):
            return apology("Not enough funds")

        # Add purchase to database
        db.execute(
            "INSERT INTO purchases (user_id, symbol, name, price, amount, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
            session["user_id"],
            quote["symbol"],
            quote["name"],
            quote["price"],
            shares,
            datetime.datetime.now(),
        )
        db.execute(
            "UPDATE users SET cash = ? WHERE id = ?",
            fundsavailable - (quote["price"] * int(shares)),
            session["user_id"],
        )

        return redirect("/")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    purchases = db.execute(
        "SELECT symbol, name, price, amount, action, timestamp FROM purchases where user_id = ?",
        session["user_id"],
    )
    for p in purchases:
        p["action"] = "Buy" if p["action"] == 1 else "Sell"
    return render_template("history.html", purchases=purchases)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    if request.method == "GET":
        return render_template("quote.html", quote="", val=0)
    if request.method == "POST":
        symbol = request.form.get("symbol")
        if symbol is None or len(symbol) == 0:
            return apology("Enter symbol for lookup.")

        quote = lookup(symbol)
        if quote != None:
            quotetext = (
                "A share of " + quote["name"] + " (" + quote["symbol"] + ") costs "
            )
        else:
            return apology("Symbol not found.")
        print(quote["price"])
        return render_template("quote.html", quote=quotetext, val=quote["price"])


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username") or len(request.form.get("username")) == 0:
            return apology("Must provide username!")

        # Ensure password was submitted
        elif not request.form.get("password") or len(request.form.get("password")) == 0:
            return apology("Must provide password!")

        elif weak_password(request.form.get("password")):
            return apology(
                "Weak password! Must contain more than 5 characters, in mixed case, have letters and numbers."
            )

        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("You must confirm the password")

        username = request.form.get("username")
        user = db.execute(
            "SELECT count(*) as cnt FROM users WHERE username = ?", username
        )
        print(user[0]["cnt"])
        if user[0]["cnt"] > 0:
            return apology("User already exists.")
        # If all checks passed - add new user

        pwdhash = generate_password_hash(request.form.get("password"))
        db.execute("INSERT INTO users(username, hash) VALUES (?, ?)", username, pwdhash)
        return redirect("/login")

    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    if request.method == "GET":
        symbols = db.execute(
            "SELECT DISTINCT symbol FROM purchases where user_id = ?",
            session["user_id"],
        )
        return render_template("sell.html", symbols=symbols)
    if request.method == "POST":
        symbol = request.form.get("symbol")
        if symbol is None or len(symbol) == 0:
            return apology("Select symbol")
        shares = request.form.get("shares")
        if shares == None or int(shares) < 1:
            return apology("Invalid amount (must be > 0)")

        quote = lookup(symbol)
        if quote == None:
            return apology("Not existing symbol")

        fundsavailable = db.execute(
            "SELECT cash FROM users where id = ?", session["user_id"]
        )[0]["cash"]

        available = db.execute(
            "SELECT SUM(amount * action) available FROM purchases where user_id = ? and symbol = ?",
            session["user_id"],
            symbol,
        )
        if int(shares) > available[0]["available"]:
            return apology("Not enough shares to sell")

        # Add sell transaxction to database
        db.execute(
            "INSERT INTO purchases (user_id, symbol, name, price, amount, timestamp, action) VALUES (?, ?, ?, ?, ?, ?, ?)",
            session["user_id"],
            quote["symbol"],
            quote["name"],
            quote["price"],
            shares,
            datetime.datetime.now(),
            -1,
        )
        db.execute(
            "UPDATE users SET cash = ? WHERE id = ?",
            fundsavailable + (quote["price"] * int(shares)),
            session["user_id"],
        )

        return redirect("/")
