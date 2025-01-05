import brokencameraphone.lib.db as db
import brokencameraphone.lib.mailing as mailing
import brokencameraphone.lib.helpers as helpers

import bcrypt
import uuid
import re
import time
import string

from flask import Flask, session, request, flash, current_app, abort
from flask.helpers import url_for
from flask.templating import render_template
from werkzeug.utils import redirect

CONFIRMATION_SUBJECT = "Welcome to Whispering Cameraphone!"
DISPLAY_NAME_ALLOWED_CHARS = string.ascii_letters + string.digits + " _-!+=?<>():;#"
PASSWORD_RESET_SUBJECT = "Reset your password"
PASSWORD_MIN_LENGTH = 6

def register_routes(app: Flask):
    @app.get("/login")
    def login_get():
        app.logger.info(f"rendering login get")

        return render_template("login.html")

    @app.post("/login")
    def login_post():
        email = request.form["email"]
        password = request.form["password"]

        if password == "":
            return render_template("login.html", error="Enter your password")
        if email == "":
            return render_template("login.html", error="Enter your email")

        user = db.query(
            """
            select * from users
            where email = ?
            """, [email], one=True)

        if user is None:
            return render_template("login.html", error="No user exists with that email address.")

        if validate_password(password, hashed_passwd = user["password"]): # type: ignore
            session["email"] = email
            session["user_id"] = int(user["id"]) # type: ignore
            session["name"] = user["display_name"] # type: ignore
            flash("You were successfully logged in.")
            session.permanent = True
        else:
            return render_template("login.html", error="That's the wrong password!")

        return redirect(url_for("index"))

    @app.post("/register")
    def register_post():
        email = request.form["email"]
        password = request.form["passwd"]
        password_check = request.form["passwd_check"]
        name = request.form["name"]

        user = db.query(
            """
            select * from users
            where email = ?
            """, [email], one=True)

        if user is not None:
            flash("A user already exists with that email! Is it you...?", category="error")
            return redirect(url_for("login_get"))

        if (err_name := check_name(name=name)) is not None:
            flash(err_name, category="error")
            return redirect(url_for("login_get"))

        if (err_email := check_email(email=email)) is not None:
            flash(err_email, category="error")
            return redirect(url_for("login_get"))

        if password != password_check:
            flash("Your passwords don't match - one of them was probably misspelled.", category="error")
            return redirect(url_for("login_get"))

        if (err_pass := check_password(password=password)) is not None:
            flash(err_pass, category="error")
            return redirect(url_for("login_get"))

        hashed = hash_password(password)
        confirmation_code = str(uuid.uuid4())

        current_app.logger.info(f"created user {email}")

        db.query(
            """
            insert into users (email, password, display_name, email_confirmation_code)
            values (?, ?, ?, ?)
            """,
            [email, str(hashed, encoding="utf-8"), name, confirmation_code], commit=True)

        session["email"] = email

        user = db.query(
            """
            select * from users
            where email = ?
            """, [email], one=True)

        session["user_id"] = int(user["id"]) # type: ignore
        session["name"] = name

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
        set has_confirmed_email = 1,
        email_confirmation_code = ?
        where id = ?
        """, [None, user["id"]], commit=True) # type: ignore

        flash("Thanks for that. Your email is now confirmed.")

        return redirect(url_for("index"))

    @app.get("/resend-confirmation")
    def get_resend_confirmation():
        if "user_id" not in session:
            return redirect(url_for("login_get"))

        new_confirmation_code = str(uuid.uuid4())

        db.query(
            """
            update users
            set email_confirmation_code = ?
            where id = ?
            """, [new_confirmation_code, session["user_id"]], commit=True)

        user = db.query(
        """
        select *
        from users
        where id = ?
        """, [session["user_id"]], one=True)

        if user == None:
            return redirect(url_for("index"))

        ok, err = send_confirmation_email(
            session["user_id"],
            user["display_name"], # type: ignore
            new_confirmation_code) # type: ignore

        if ok:
            flash("Confirmation email re-sent. Please give it a few minutes to be delivered.")
        else:
            flash(f"Couldn't resend confirmation. {err}") # type: ignore

        return redirect(url_for("index"))

    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for("index"))

    ###############
    # Users pages #
    ###############

    @app.get("/profile") # Any old redirects go to the new profile system
    def profile_redirect():
        return redirect("/user")

    @app.get("/user") # Redirect to here to get to the users personal profile page
    def profile_get_check():
        if "user_id" in session: # User logged in so show profile
            return redirect("/user/" + session["name"]) # Redirect to /user/<their username>
        else:
            return redirect(url_for("index")) # Redirect to home

    @app.get("/user/<name>")
    def profile_get(name):
        the_user = db.query(
            """
            select * from users
            where display_name = ?
            """, [name], one=True)

        if the_user is not None:
            # The user exists in the database

            # Does this user want to show their stats?
            show_stats = the_user["show_stats"] == 1 # type: ignore

            if "user_id" in session: # Someone logged in?
                webhooks = db.query(
                    """
                    select display_name, webhook from webhooks
                    where user_id = ?
                    """, [session["user_id"]])

                get_webhooks = [(x["display_name"], x["webhook"], x["display_name"].replace(" ", "")) for x in webhooks] # type: ignore

                # The user matches the profile?
                own_profile = the_user["id"] == session["user_id"] # type: ignore

                return render_template("user.html",
                                        user_id = session["user_id"],
                                        name = name,
                                        own_profile = own_profile,
                                        show_stats = show_stats,
                                        webhooks = get_webhooks,
                                        webhook_count = len(get_webhooks))
            else:
                return render_template("user.html",
                                        name = name,
                                        show_stats = show_stats)
        else:
            abort(404)

    @app.post("/user/update_preferences")
    def preferences_post():
        pref = request.form.get("public_stats") == "yes"

        db.query(
            """
            update users set show_stats = ?
            where id = ?
            """, [pref, session["user_id"]], commit = True)

        return redirect("/user")

    @app.post("/user/update_details")
    def update_details_post():
        if (new_name := request.form.get("new_username", default="")) != "":
            if new_name == session["name"]:
                flash("Your new display name is the same as your current one.")
                return(redirect("/user"))

            if (error := check_name(new_name)) is not None:
                flash(error)
                return redirect("/user")

            db.query(
                """
                update users set display_name = ?
                where id = ?
                """, [new_name, session["user_id"]], commit = True)

            del session["name"]
            session["name"] = new_name

        # Need to understand if the new email address is legit and verify it. But cannot change current one to it just yet.
        if (new_email := request.form.get("new_email")) != "":
            flash("Changing your email is not possible at this time.")
            return redirect("/user")

        flash("Your details have been updated.")
        return redirect("/user")

    @app.post("/user/update_password")
    def update_password_post():
        fail = False
        if (curr_passwd := request.form.get("current_passwd", default="")) == "":
            flash("You must enter you current password.")
            fail = True
        elif (new_passwd := request.form.get("passwd", default="")) == "":
            flash("You must enter a new password.")
            fail = True
        elif (new_passwd_check := request.form.get("passwd_check")) == "":
            flash("You must repeat your new password.")
            fail = True
        elif new_passwd != new_passwd_check:
            flash("The passwords do not match.")
            fail = True
        elif curr_passwd == new_passwd:
            flash("Your current password matches your new one.")
            fail = True

        if not fail:
            if (pass_error := check_password(new_passwd)) is None: # Does the password meet the requirements?
                if validate_password(curr_passwd, user_id = session["user_id"]): # Is the current password correct?
                    hashed_passwd = hash_password(new_passwd)
                    db.query(
                        """
                        update users set password = ?
                        where id = ?
                        """, [str(hashed_passwd, encoding="utf-8 "), session["user_id"]], commit=True)

                    flash("Your password has been updated. Add send email notif.")
                    #### SEND EMAIL ####
                else:
                    flash("Current password is incorrect.")
            else:
                flash(pass_error)

        return redirect("/user")

    # To-do: Keep same option selected and input boxes same if filled
    @app.post("/user/update_webhook")
    def webhook_post():
        option = request.form.get("webhook_selector")
        if option is None:
            flash("Please select an option")
            return redirect("/user")

        if request.form.get("submit") is not None:
            # Submit clicked, not delete
            friendly = request.form.get("friendly_name", default="")
            webhook = request.form.get("webhook_name", default="")

            if option == "add_new":
                # Add new webhook to db
                if (err := check_webhook_submission(webhook, friendly)) is False:
                    db.query(
                        """
                        insert into webhooks (user_id, webhook, display_name)
                        values (?, ?, ?)
                        """, [session["user_id"], webhook, friendly], commit = True)

                    flash(f"The webhook '{friendly}' was added to your profile.")
                else:
                    flash(err)
            else:
                # Update currently selected one
                # Add new webhook to db
                if (err := check_webhook_submission(webhook, friendly, update = True)) is False:
                    test = db.query(
                        """
                        update webhooks
                        set webhook = ?, display_name = ?
                        where user_id = ? and display_name = ?
                        """,
                        [webhook, friendly, session["user_id"], option], commit = True)
                    flash(f"Webhook '{friendly}' has been updated.")
                else:
                    flash(err)
        elif request.form.get("delete") is not None:
            # Delete clicked
            db.query(
                """
                delete from webhooks
                where user_id = ? and display_name = ?
                """, [session["user_id"], option], commit = True)

            flash(f"Webhook '{option}' has been deleted.")
        else:
            # Something odd happened..?
            flash("Something went wrong with that request. Please try again later.")

        return redirect("/user")

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

# Useful functions
def check_password(password: str) -> str | None:
    """
    Checks password for certain conditions. This does not check hashes!
    Will return error as a string if there is one. Else returns None.
    """

    if len(password) < PASSWORD_MIN_LENGTH:
        return f"Your password must be at least {PASSWORD_MIN_LENGTH} characters long"

    return None

def check_name(name: str) -> str | None:
    """
    Checks the display name. Will return error as a string if there is one. Else returns None.
    """

    if not all(ch in DISPLAY_NAME_ALLOWED_CHARS for ch in name):
        return f"Your display name can only contain characters in '{DISPLAY_NAME_ALLOWED_CHARS}'."

    if len(name) < 3:
        return "Your display name must be at least three characters long."

    return None

def check_email(email: str) -> str | None:
    """
    Checks the email. Will return error as a string if there is one, else None.
    """

    if any(ch in "()'\"" or ch.isspace() for ch in email):
        return f"Your email address contains some invalid characters."

    return None

def validate_password(passwd: str,
                      hashed_passwd: str | None = None,
                      user_id: int | None = None) -> bool:
    """
    Checks the users password against the database and returns True if valid, and False if not.

    Must be given a `password`. Must also provide `hashed_password` or `user_id` for a lookup.
    """

    if hashed_passwd is None: # Look up the hashed password from the database
        hashed_passwd = db.query(
            """
            select password from users
            where id = ?
            """, [user_id], one = True)["password"] # type: ignore

    return bcrypt.checkpw(
        passwd.encode("utf-8"),
        hashed_passwd.encode("utf-8"), # type: ignore
    )

def hash_password(passwd: str) -> bytes:
    """
    Hashes the users password and returns the salted+hashed string.
    """

    return bcrypt.hashpw(passwd.encode("utf-8"), bcrypt.gensalt())

def check_webhook_submission(webhook: str, friendly: str, update: bool = False):
    """
    Pass in a webhook display name and webhook and it will return `False` if valid, else return the error.

    Use `update = True` when updating a current webhook.
    """

    pattern = r'[^a-zA-Z0-9\s]'

    check_friendly = db.query(
        """
        select * from webhooks
        where user_id = ? and display_name = ?
        """,  [session["user_id"], friendly], one = True)

    check_webhook = db.query(
        """
        select * from webhooks
        where user_id = ? and webhook = ?
        """, [session["user_id"], webhook], one = True)

    if friendly == "":
        return "You must enter a friendly name."
    elif webhook == "":
        return "You must provide webhook endpoint URL."
    elif check_friendly is not None and update is False:
        return f"You already have a webhook called {friendly}."
    elif check_webhook is not None and update is False:
        return f"You already have a webhook with this endpoint called '{check_webhook['display_name']}'." # type: ignore
    elif re.findall(pattern, friendly) != []:
        return "Your friendly name can only contain a-z, 0-9, and spaces."
    elif len(friendly) > 20:
        return "Your friendly name can be up to 20 characters long."

    return False

def send_confirmation_email(user_id, name, confirmation_code):
    url = current_app.config["ROOT_URL"] + "/verify/" + confirmation_code

    content = render_template(
        "mail/email-confirmation.html",
        name=name,
        url=url)

    return mailing.send_email(
        user_id,
        CONFIRMATION_SUBJECT,
        content)

def send_reset_password_email(user_id, name, code):
    url = current_app.config["ROOT_URL"] + "/reset-password/" + code

    content = render_template(
        "mail/password-reset.html",
        name=name,
        url=url)

    return mailing.send_email(
        user_id,
        PASSWORD_RESET_SUBJECT,
        content)
