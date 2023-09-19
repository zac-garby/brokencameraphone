import os
import secrets
import lib.db as db

from lib import users, lobby, game

from flask import Flask, session
from flask.helpers import url_for
from flask.templating import render_template
from werkzeug.utils import redirect

app = Flask(__name__)

app.config.from_mapping(
    SECRET_KEY=secrets.token_hex(),
    DATABASE=os.path.join(app.instance_path, "bcp.sqlite"),
    UPLOAD_FOLDER=os.path.join(app.instance_path, "photos")
)

try:
    os.makedirs(app.instance_path)
except OSError:
    pass

try:
    os.makedirs(app.config["UPLOAD_FOLDER"])
except OSError:
    pass

db.init_app(app)

users.register_routes(app)
lobby.register_routes(app)
game.register_routes(app)

@app.route("/")
def index():
    if "user_id" in session:
        games = db.query("""
            select * from games
            inner join participants as p on games.id = p.game_id
            where p.user_id = ?
                         """,
                         [session["user_id"]])
        
        return render_template("index.html",
                               games=games,
                               user_id=session["user_id"])
    else:
        return redirect(url_for("login_get"))
