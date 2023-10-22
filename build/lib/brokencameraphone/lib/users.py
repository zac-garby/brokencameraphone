import brokencameraphone.lib.db as db
import bcrypt

from flask import Flask, session, request, flash
from flask.helpers import url_for
from flask.templating import render_template
from werkzeug.utils import redirect

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

        db.query("insert into users (email, password, display_name) values (?, ?, ?)",
                [email, str(hashed, encoding="utf-8"), name],
                commit=True)
        
        session["email"] = email

        user = db.query("select * from users where email = ?", [email], one=True)
        session["user_id"] = int(user["id"]) # type: ignore

        flash("Your account has been made, and you've been logged in. Welcome to Broken Cameraphone!")

        return redirect(url_for("index"))

    @app.route("/logout")
    def logout():
        del(session["email"])
        del(session["user_id"])
        return redirect(url_for("index"))