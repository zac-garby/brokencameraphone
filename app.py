import os
import db

from lib import users, lobby

from flask import Flask, session
from flask.helpers import url_for
from flask.templating import render_template
from werkzeug.utils import redirect

app = Flask(__name__)

app.config.from_mapping(
    SECRET_KEY="dev",
    DATABASE=os.path.join(app.instance_path, "bcp.sqlite")
)

try:
    os.makedirs(app.instance_path)
except OSError:
    pass

db.init_app(app)

users.register_routes(app)
lobby.register_routes(app)

@app.route("/")
def index():
    if "user_id" in session:
        return render_template("index.html")
    else:
        return redirect(url_for("login_get"))
