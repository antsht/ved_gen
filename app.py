import datetime
import io
import os

import openpyxl
from flask import Flask, flash, redirect, render_template, request, send_file, session

from werkzeug.security import check_password_hash, generate_password_hash

from database import get_vedomosti, get_students
from xlsxhelper import generate_xlsx_ved, upload_xlsx_ved
from flask_session import Session
from helpers import apology, format_hrs, login_required, lookup, usd, weak_password
from sql import SQL

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd
app.jinja_env.filters["hrs"] = format_hrs


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
# db = SQL("sqlite:///finance.db")
db = SQL("sqlite:///vedDB.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "GET":
        vedomosti = get_vedomosti()
        if request.args.get("ved") is not None and len(request.args.get("ved")) > 0:
            students = get_students(request.args.get("ved"))
            return render_template("index.html", vedomosti=vedomosti, students=students)
        else:
            return render_template("index.html", vedomosti=vedomosti, students=[])
    if request.method == "POST":
        print(request.form.get("id"))
        return redirect("/vedomost?id=" + request.form.get("id"))


@app.route("/vedomost", methods=["GET", "POST"])
@login_required
def vedomost():
    if request.method == "GET":
        if not request.args.get("id") or len(request.args.get("id")) == 0:
            return redirect("/")
        id = int(request.args.get("id"))
        vedomosti = get_vedomosti(id)
        return render_template("vedomost.html", vedomosti=vedomosti)
    if request.method == "POST":
        id = int(request.form.get("id"))

        xlsx_file = generate_xlsx_ved(id)
        flash("XLS generated", category="message")
        return send_file(xlsx_file, download_name="output.xlsx", as_attachment=True)


@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    if request.method == "GET":
        return render_template("upload.html")
    if request.method == "POST":
        if "file" not in request.files:
            return "No file part"
        file = request.files["file"]
        if file.filename == "":
            return "No selected file"
        if file:
            if upload_xlsx_ved(file):
                return "File uploaded successfully"
            return "Error during processing uploaded XLSX file"


@app.route("/history")
@login_required
def history():
    return render_template("history.html", history_records=None)


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
