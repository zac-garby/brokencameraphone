import brokencameraphone.lib.db as db
import brokencameraphone.lib.mailing as mailing
import brokencameraphone.lib.helpers as helpers
import bcrypt
import uuid
import string

from flask import Flask, session, request, flash, current_app
from flask.helpers import url_for
from flask.templating import render_template
from werkzeug.utils import redirect

DISPLAY_NAME_ALLOWED_CHARS = string.ascii_letters + string.digits + " _-!+=?<>():;#"

CONFIRMATION_SUBJECT = "Welcome to Whispering Cameraphone!"
CONFIRMATION_EMAIL = """<p>Welcome to Whispering Cameraphone, {name}!</p>

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

PASSWORD_RESET_SUBJECT = "Reset your password"
PASSWORD_RESET_EMAIL = """<p>
Hi {name}. You have requested that your password for
<a href='https://whisperingcameraphone.com'>Whispering Cameraphone</a>
be reset.
</p>

<ul>
  <li>
    <p>
      If this was you, and you would indeed like to reset it, click
      the link below or copy it into your browser's address bar:
    </p>
    <p><a href="{url}">{url}</a></p>
  </li>
  <li>
    <p>
      If you haven't requested a password reset, don't worry! Somebody
    may be trying to get into your account, but as long as they don't
    have access to this email's inbox, they won't be able to.
    </p>
</ul>
  
<p>
  If you have any concerns or issues resetting your password or
  are worried that somebody may have access to your account, please
  get in touch.
</p>
  
<p>Best,</p>

<p>
Zac
(<a href="https://zacgarby.co.uk">https://zacgarby.co.uk</a>)
</p>"""

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
        
        if not all(ch in DISPLAY_NAME_ALLOWED_CHARS for ch in name):
            return render_template("login.html", error=f"Your display must only contain the following characters: {DISPLAY_NAME_ALLOWED_CHARS}")

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

        ok, err = send_confirmation_email(
            session["user_id"],
            name,
            confirmation_code
        )

        if not ok:
            flash(f"Couldn't send confirmation email. {err}")

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
    
    @app.get("/resend-confirmation")
    def get_resend_confirmation():
        if "user_id" not in session:
            return redirect(url_for("login_get"))
        
        user = db.query(
        """
        select email_confirmation_code
        from users
        where id = ?
        """, [session["user_id"]], one=True)

        if user == None:
            return redirect(url_for("index"))
        
        ok, err = send_confirmation_email(
            session["user_id"],
            user["display_name"], # type: ignore
            user["email_confirmation_code"]) # type: ignore
        
        if ok:
            flash("Confirmation email re-sent. Please give it a few minutes to be delivered.")
        else:
            flash(f"Couldn't resend confirmation. {err}") # type: ignore
        
        return redirect(url_for("index"))

    @app.route("/logout")
    def logout():
        del(session["email"])
        del(session["user_id"])
        return redirect(url_for("index"))
    
    @app.get("/reset-password")
    def request_reset_password():
        email = request.args.get("email", default="")

        recipient = db.query(
        """
        select * from users
        where email = ?
        """, [email], one=True)

        if recipient != None:
            code = str(uuid.uuid4())

            ok, err = send_reset_password_email(
                recipient["id"], # type: ignore
                recipient["display_name"], # type: ignore
                email,
                code
            )

            if not ok:
                flash(f"Couldn't send password reset confirmation email. {err}")
                return redirect(url_for("index"))
            
            db.query(
            """
            update users
            set reset_password_code = ?
            where id = ?
            """, [code, recipient["id"]], commit=True) # type: ignore
        
        flash(f"If the given email {email} is associated with an account, we've sent a confirmation email to that address. Check that email for the next steps in resetting your password.")

        return redirect(url_for("index"))
    
    @app.get("/reset-password/<code>")
    def get_reset_password(code):
        user = db.query(
        """
        select * from users
        where reset_password_code = ?
        """, [code], one=True)

        if user == None:
            flash("The given password reset code is not valid! Maybe you've requested a new one since, or typed this one into the address bar incorrectly?")
            return redirect(url_for("index"))
        
        return render_template("reset-password.html", user=user, code=code, user_id=user["id"]) # type: ignore
    
    @app.post("/reset-password/<code>")
    def post_reset_password(code):
        password = request.form["password"]
        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

        db.query(
        """
        update users
        set password = ?, reset_password_code = NULL
        where reset_password_code = ?
        """, [hashed, code])

        flash("Your password has been successfully updated.")

        return redirect(url_for("index"))

def send_confirmation_email(user_id, name, confirmation_code):
    url = current_app.config["ROOT_URL"] + "/verify/" + confirmation_code
    return mailing.send_email(user_id,
                              CONFIRMATION_SUBJECT,
                              CONFIRMATION_EMAIL.format(
                                  url=url,
                                  name=name
                              ))

def send_reset_password_email(user_id, name, email, code):
    url = current_app.config["ROOT_URL"] + "/reset-password/" + code
    new_request_url = current_app.config["ROOT_URL"] + "/request-password-reset/" + email

    return mailing.send_email(user_id,
                              PASSWORD_RESET_SUBJECT,
                              PASSWORD_RESET_EMAIL.format(
                                  url=url,
                                  new_request=new_request_url,
                                  name=name
                              ))