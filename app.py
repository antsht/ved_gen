import os
import datetime
from sql import SQL

from flask import Flask, flash, redirect, render_template, request, session, send_file
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd, weak_password, format_hrs

import openpyxl
from openpyxl.styles import Alignment
from openpyxl.worksheet.datavalidation import DataValidation
import io


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
#db = SQL("sqlite:///finance.db")
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
        vedomosti = db.execute("SELECT vedomosti.id, vedomosti.group_id, vedomosti.discipline, vedomosti.control_type, vedomosti.name_of_ekzaminator, vedomosti.hours_total, vedomosti.control_date, groups.name as g_name, facultets.name as f_name FROM vedomosti LEFT JOIN groups on vedomosti.group_id = groups.id LEFT JOIN facultets ON groups.facultet = facultets.id;")
        if request.args.get("ved") is not None and len(request.args.get("ved"))>0:
            students = db.execute("SELECT vedomosti.id, students.student_number, students.full_name, results.result FROM vedomosti LEFT JOIN groups ON groups.id = vedomosti.group_id LEFT JOIN students ON students.group_id = groups.id LEFT JOIN results ON students.id = results.student_id and vedomosti.id = results.vedomost_id WHERE vedomosti.id = ?;", request.args.get("ved") )
            return render_template(
                "index.html", 
                vedomosti=vedomosti,
                students=students)
        else:
            return render_template(
                "index.html", 
                vedomosti=vedomosti,
                students=[])
    if request.method == "POST":
        print(request.form.get("id"))
        return redirect("/vedomost?id=" + request.form.get("id"))
    

@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    if request.method == "GET":
        return render_template(
            "upload.html")
    if request.method == 'POST':
        if 'file' not in request.files:
            return 'No file part'
        file = request.files['file']
        if file.filename == '':
            return 'No selected file'
        if file:
            wb = openpyxl.load_workbook(file)
            ws = wb.active
            data = ws.values
            # process data
            for row in data:              
                if row[0] is not None and row[1] is not None and isinstance(row[0], int) and isinstance(row[1], int) and row[3] is not None and len(row[3])>0:
                    print(f"{row[0]}, {row[1]}, {row[3]}")
                    res = db.execute("SELECT * FROM results WHERE vedomost_id = ? AND student_id = ?;", ws["B1"], row[1])
                    if len(res) == 0:
                        db.execute("INSERT INTO results (vedomost_id, student_id, result) VALUES (?,?,?);", ws["B1"], row[1], row[3]);
                    else:
                        db.execute("UPDATE results SET result = ? WHERE vedomost_id = ? AND student_id = ?;",row[3], ws["B1"], row[1])
            return 'File uploaded successfully'
    
    
@app.route("/vedomost", methods=["GET", "POST"])
@login_required
def vedomost():
    if request.method == "GET":
        if not request.args.get("id") or len(request.args.get("id")) == 0:
            return redirect("/")
        
        id = int(request.args.get("id"))
        vedomosti = db.execute("SELECT vedomosti.id, vedomosti.group_id, vedomosti.discipline, vedomosti.control_type, vedomosti.name_of_ekzaminator, vedomosti.hours_total, vedomosti.control_date, groups.name as g_name, facultets.name as f_name FROM vedomosti LEFT JOIN groups on vedomosti.group_id = groups.id LEFT JOIN facultets ON groups.facultet = facultets.id WHERE vedomosti.id = ?;", id  )
        #print(request.args.get("id"))
        #print(vedomosti)
        return render_template(
            "vedomost.html", 
            vedomosti=vedomosti)
    if request.method == "POST":
        id=int(request.form.get("id"))
        vedomost = db.execute("SELECT vedomosti.id, vedomosti.group_id, vedomosti.discipline, vedomosti.control_type, vedomosti.name_of_ekzaminator, vedomosti.hours_total, vedomosti.control_date, groups.name as g_name, facultets.name as f_name FROM vedomosti LEFT JOIN groups on vedomosti.group_id = groups.id LEFT JOIN facultets ON groups.facultet = facultets.id WHERE vedomosti.id = ?;", id  )
        header_data = [
            ['ID', vedomost[0]["id"]],
            ['Facultet name', vedomost[0]["f_name"]],
            ['Group ID', vedomost[0]["group_id"]],
            ['Group name', vedomost[0]["g_name"]],
            ['Discipline', vedomost[0]["discipline"]],
            ['Type', vedomost[0]["control_type"]],
            ['Teacher', vedomost[0]["name_of_ekzaminator"]],
            ['Hours', vedomost[0]["hours_total"]],
            ['Date', vedomost[0]["control_date"]],
        ]
        workbook = openpyxl.Workbook()
        worksheet = workbook.active

        row_number = 1
        for header_row in header_data:
            worksheet[f"A{row_number}"] = header_row[0]
            worksheet[f"B{row_number}"] = header_row[1]
            worksheet.merge_cells(f"B{row_number}:F{row_number}")
            worksheet[f"A{row_number}"].alignment = Alignment(horizontal='right') 
            worksheet[f"B{row_number}"].alignment = Alignment(horizontal='center') 

            row_number +=1 

        # Create a list of choices
        choices = ['']
        results = db.execute("SELECT name FROM sprav_result;")
        for res in results:
            choices.append(res["name"])        

        # Create a Data Validation rule
        dv = DataValidation(type="list", formula1=f'"{",".join(choices)}"', allow_blank=True)
        
        #dv = DataValidation(type="list", formula1='"Zachteno,Horosho,Otlichno"', allow_blank=True)

        # Add the Data Validation rule to the worksheet
        worksheet.add_data_validation(dv)

        students = db.execute("SELECT students.student_number, students.full_name FROM vedomosti JOIN students ON students.group_id = vedomosti.group_id WHERE vedomosti.id = ?;", id  )
        row_number += 1
        worksheet[f"A{row_number}"] = "Код ведомости"
        worksheet[f"B{row_number}"] = "Студномер"
        worksheet[f"C{row_number}"] = "ФИО"
        worksheet[f"D{row_number}"] = "Результат"
        row_number += 1
        stud_number = 1
        for student in students:
            worksheet[f"A{row_number}"] = stud_number
            worksheet[f"B{row_number}"] = student["student_number"]
            worksheet[f"C{row_number}"] = student["full_name"]
            worksheet[f"D{row_number}"] = ""
            dv.add(worksheet[f"D{row_number}"])
            row_number += 1
            stud_number += 1
            

        output = io.BytesIO()
        workbook.save(output)
        output.seek(0)
        flash("XLS generated", category="message")
        return send_file(output, download_name='output.xlsx', as_attachment=True)


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