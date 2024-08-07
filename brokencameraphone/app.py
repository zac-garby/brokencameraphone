import os
import brokencameraphone.lib.db as db
import brokencameraphone.lib.helpers as helpers

from brokencameraphone.lib import users, lobby, game

from flask import Flask, session
from flask.helpers import url_for
from flask.templating import render_template
from werkzeug.utils import redirect

app = Flask(__name__)

app.config.from_mapping(
    SECRET_KEY=os.getenv("SECRET_KEY", default="dev"),
    DATABASE=os.path.join(app.instance_path, "bcp.sqlite"),
    UPLOAD_FOLDER=os.path.join(app.instance_path, "photos"),
    ROOT_URL="https://whisperingcameraphone.com"
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
    if "user_id" not in session:
        return redirect(url_for("login_get"))
    
    user = db.query(
    """
    select has_confirmed_email, display_name, email
    from users
    where id = ?
    """, [session["user_id"]], one=True)

    if user == None:
        return redirect(url_for("login_get"))
    
    if user["has_confirmed_email"] == 0: # type: ignore
        return render_template("needs-email-confirmation.html",
                               name=user["display_name"], # type: ignore
                               email=user["email"]) # type: ignore
    
    games = db.query("""
    select
        games.*, p.*,
        case
            when archived.user_id is not null then 1 else 0
        end as is_archived
    from
        games
    inner join participants as p on games.id = p.game_id
    left join archived on games.id = archived.game_id and archived.user_id = p.user_id
    where p.user_id = ? and is_archived = 0
                    """,
                    [session["user_id"]])
    
    return render_template("index.html",
                           games=games,
                           user_id=session["user_id"])

@app.get("/about")
def get_about():
    if "user_id" in session:
        return render_template("about.html",
                            user_id=session["user_id"])
    else:
        return render_template("about.html")

@app.get("/archive")
@helpers.logged_in
def get_archive():
    games = db.query("""
        select
            games.*, p.*,
            case
                when archived.user_id is not null then 1 else 0
            end as is_archived
        from
            games
        inner join participants as p on games.id = p.game_id
        left join archived on games.id = archived.game_id and archived.user_id = p.user_id
        where p.user_id = ?
                        """,
                        [session["user_id"]])

    return render_template("archive.html",
                            games=games,
                            user_id=session["user_id"])

@app.errorhandler(404)
def error_404(e):
    user_id = session["user_id"] if "user_id" in session else None
    return render_template("404.html", user_id=user_id)