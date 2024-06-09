import brokencameraphone.lib.db as db
import brokencameraphone.lib.helpers as helpers

from flask import Flask, session, abort, request, flash
from flask.helpers import url_for
from flask.templating import render_template
from werkzeug.utils import redirect

def register_routes(app: Flask):
    @app.get("/profile") # Any old redirects go to the new profile system
    def profile_redirect():
        return redirect("/user")

    @app.get("/user")
    def profile_get_check():
        if "user_id" in session: # user logged in
            return redirect("/user/" + session["name"]) # Redirect to /user/username
        else:
            return redirect(url_for("index")) # Redirect to home

    @app.get("/user/<name>")
    def profile_get(name):
        get_user = db.query("select * from users where display_name == ?", (name,), one=True)
        if get_user is not None: # The user exists in the database
            own_profile = False
            if "user_id" in session: # Someone logged in?
                if get_user["id"] == session["user_id"]: # The user matches the profile?
                    own_profile = True

                return render_template("user.html", 
                                        user_id = session["user_id"],
                                        name = name,
                                        own_profile = own_profile)
            else:
                return render_template("user.html", 
                                        name = name,
                                        own_profile = False)
        else:
            abort(404)