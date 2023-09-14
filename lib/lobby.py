import db
import random

from flask import Flask, session, request, flash
from flask.helpers import url_for
from flask.templating import render_template
from werkzeug.utils import redirect

def register_routes(app: Flask):
    @app.post("/game")
    def game_no_param_post():
        return redirect("/game/" + request.form["join-code"]) # type: ignore

    @app.get("/game/<joincode>")
    def game_get(joincode):
        if "user_id" not in session:
            return redirect(url_for("index"))

        game = db.query("select * from games where join_code = ?",
                        [joincode], one=True)
        
        if game is None:
            flash("The game you tried to join does not exist.")
            return redirect(url_for("index"))
        
        participant = db.query("select * from participants where user_id = ? and game_id = ?",
                            [session["user_id"], game["id"]], one=True) # type: ignore
        
        state = int(game["state"]) # type: ignore

        if participant is None:
            # can't join - not a participant, and the game has already started
            if state > 0:
                flash("This game is already in progress!")
                return redirect(url_for("index"))
            
            # can join; game not yet started. not yet a participant, so making them one
            else:
                flash("You successfully joined the game.")
                db.query("insert into participants (user_id, game_id) values (?, ?)",
                    [session["user_id"], game["id"]], # type: ignore
                    commit=True)
                return redirect("/game/" + joincode)
        
        # rejoining a game which the user is already part of
        else:
            template = {
                0: "lobby.html",
                1: "initial-prompt.html",
                2: "photo.html",
                3: "photo-prompt.html"
            }[state]

            return render_template(template, game=game)

    @app.get("/leave-game/<joincode>")
    def leave_game_get(joincode):
        if "user_id" not in session:
            return redirect(url_for("index"))
        
        participant = db.query("""
                            select * from participants
                            inner join games on participants.game_id = games.id
                            where user_id = ? and games.join_code = ?
                            """,
                            [session["user_id"], joincode], one=True)
        
        if participant is None:
            flash("You attempted to leave a game which you're not in!")
        else:
            db.query("delete from participants where user_id = ? and game_id = ?",
                    [session["user_id"], participant["game_id"]], # type: ignore
                    commit=True)
        
        return redirect(url_for("index"))

    @app.get("/new-game")
    def new_game_get():
        if "user_id" not in session:
            return redirect(url_for("index"))
        
        code = None
        symbols = "ABCDEFGHIJKLMNLOPQRSTUVWXYZ"

        while True:
            code = "".join(random.choice(symbols) for i in range(4))
            game = db.query("select * from games where join_code = ?",
                        [code], one=True)
            if game is None:
                break
        
        db.query("insert into games (join_code, owner_id, state) values (?, ?, ?)",
                [code, session["user_id"], 0],
                commit=True)
        
        print("making game with code", code)
        return redirect(f"/game/{code}")

    @app.get("/api/lobby/<joincode>")
    def api_lobby(joincode):
        if "user_id" not in session:
            return redirect(url_for("index"))
    
        participants = db.query("""
        select display_name, users.id = g.owner_id as "is_owner" from users
        inner join participants as p on users.id = p.user_id
        inner join games as g on p.game_id = g.id
        where g.join_code = ?
                            """,
                            [joincode])

        game = db.query("""
        select * from games
        where join_code = ?
                        """,
                        [joincode], one=True)
        
        if participants != None:
            players = [ {
                "display_name": p["display_name"],
                "is_owner": p["is_owner"],
            } for p in participants ]

            return {
                "players": players,
                "joincode": joincode,
                "state": int(game["state"]) # type: ignore
            }

        return { "error": "lobby doesn't exist" }