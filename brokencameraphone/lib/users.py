import brokencameraphone.lib.db as db
import brokencameraphone.lib.mailing as mailing
import bcrypt
import uuid

from flask import Flask, session, request, flash, current_app
from flask.helpers import url_for
from flask.templating import render_template
from werkzeug.utils import redirect

CONFIRMATION_SUBJECT = "Welcome to Whispering Cameraphone!"
CONFIRMATION_EMAIL = """<p>Welcome to Whispering Cameraphone!</p>

<p>To get started, you'll need to confirm your email. Please click
the link below (or, copy it into your web browser's address bar
if you can't click it).</p>

<p><a href="{url}">{url}</a></p>

<p>Let me know if you have any problems!</p>

<p>Best,</p>

<p>
Zac
(<a href="https://zacgarby.co.uk">https://zacgarby.co.uk</a>)
</p>
"""

def register_routes(app: Flask):
    @app.get("/login")
    def login_get():
        app.logger.info(f"rendering login get")

        return render_template("login.html")

    @app.post("/login")
    def login_post():
        email = request.form["email"]
        password = request.form["password"]

        user = db.query("select * from users where email = ?",
                        [email], one=True)

        if user is None:
            return render_template("login.html", error="No user exists with that email address.")

        valid = bcrypt.checkpw(
            password.encode("utf-8"),
            user["password"].encode("utf-8"), # type: ignore
        )

        if valid:
            session["email"] = email
            session["user_id"] = int(user["id"]) # type: ignore
            flash("You were successfully logged in.")
            session.permanent = True
        else:
            return render_template("login.html", error="That's the wrong password!")
        
        return redirect(url_for("index"))

    @app.post("/register")
    def register_post():
        email = request.form["email"]
        password = request.form["password"]
        name = request.form["name"]

        user = db.query("select * from users where email = ?",
                        [email], one=True)

        if user is not None:
            return render_template("login.html", error="A user already exists with that email! Is it you..?")
        
        if len(password) < 5:
            return render_template("login.html", error="Your password must be at least 5 characters long.")
        
        if len(name) < 3:
            return render_template("login.html", error="Your display name must be at least 3 characters long.")

        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

        confirmation_code = str(uuid.uuid4())

        db.query("""
        insert into users (email, password, display_name, has_confirmed_email, email_confirmation_code)
        values (?, ?, ?, 0, ?)
        """,
        [email, str(hashed, encoding="utf-8"), name, confirmation_code],
        commit=True)
        
        session["email"] = email

        user = db.query("select * from users where email = ?", [email], one=True)
        session["user_id"] = int(user["id"]) # type: ignore

        flash(f"Your account has been made! Now you'll have to confirm your email: check your inbox at {email}.")

        send_confirmation_email(email, confirmation_code)

        return redirect(url_for("index"))
    
    @app.get("/verify/<code>")
    def get_verify(code):
        user =  db.query(
        """
        select id from users
        where email_confirmation_code = ? and has_confirmed_email = 0
        """, [code], one=True)

        if user == None:
            flash("You've already verified your email!")
            return redirect(url_for("index"))
        
        db.query(
        """
        update users
        set has_confirmed_email = 1
        where id = ?
        """, [user["id"]], commit=True) # type: ignore

        flash("Thanks for that. Your email is now confirmed.")

        return redirect(url_for("index"))

    @app.route("/logout")
    def logout():
        del(session["email"])
        del(session["user_id"])
        return redirect(url_for("index"))

def send_confirmation_email(email, confirmation_code):
    url = current_app.config["ROOT_URL"] + "/verify/" + confirmation_code
    mailing.send_email(email,
                       CONFIRMATION_SUBJECT,
                       CONFIRMATION_EMAIL.format(url=url))
