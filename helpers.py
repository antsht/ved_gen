from flask import redirect, render_template, session, flash
from functools import wraps


def apology(message, code=400):
    """Render message as an apology to user."""

    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [
            ("-", "--"),
            (" ", "-"),
            ("_", "__"),
            ("?", "~q"),
            ("%", "~p"),
            ("#", "~h"),
            ("/", "~s"),
            ('"', "''"),
        ]:
            s = s.replace(old, new)
        return s

    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_role") is None or session.get("user_role")!='admin':
            flash(message='Login as admin to register new users', category='info')
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function


def format_hrs(value):
    """Format value as Hours."""
    return f"{value:,.1f} Hrs."


def weak_password(password) -> bool:
    if (
        len(password) > 5
        and not password.isalpha()
        and not password.isnumeric()
        and password != password.swapcase()
    ):
        return False
    return True
