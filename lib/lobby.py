import lib.db as db
import lib.helpers as helpers

import random

from flask import Flask, session, request, flash
from flask.helpers import url_for
from flask.templating import render_template
from werkzeug.utils import redirect

def register_routes(app: Flask):
    @app.post("/game")
    def game_no_param_post():
        return redirect("/game/" + request.form["join-code"]) # type: ignore

    @app.get("/leave-game/<joincode>")
    @helpers.logged_in
    @helpers.with_participant("participant")
    def leave_game_get(joincode, participant):
        if participant is None:
            flash("You attempted to leave a game which you're not in!")
        else:
            db.query("delete from participants where user_id = ? and game_id = ?",
                    [session["user_id"], participant["game_id"]], # type: ignore
                    commit=True)
        
        return redirect(url_for("index"))
    
    @app.get("/start-game/<joincode>")
    @helpers.logged_in
    @helpers.with_participant("participant")
    @helpers.lobby_owner(otherwise="index")
    def start_game_get(joincode, participant):
        if participant is None:
            flash("You attempted to start a game which you're not in!")
        else:
            db.query("update games set state = 1 where join_code = ?",
                     [joincode],
                     commit=True)

        return redirect("/game/" + joincode)


    @app.get("/new-game")
    @helpers.logged_in
    def new_game_get():
        code = None
        symbols = "ABCDEFGHIJKLMNLOPQRSTUVWXYZ"

        while True:
            code = "".join(random.choice(symbols) for i in range(4))
            game = db.query("select * from games where join_code = ?",
                        [code], one=True)
            if game is None:
                break
        
        db.query("insert into games (join_code, owner_id, state, current_round) values (?, ?, 0, 0)",
                [code, session["user_id"]],
                commit=True)
        
        print("making game with code", code)
        return redirect(f"/game/{code}")

    @app.get("/api/lobby/<joincode>")
    @helpers.logged_in
    @helpers.with_game("game")
    def api_lobby(joincode, game):
        participants = db.query("""
        select display_name, users.id = g.owner_id as "is_owner" , p.has_submitted from users
        inner join participants as p on users.id = p.user_id
        inner join games as g on p.game_id = g.id
        where g.join_code = ?
                            """,
                            [joincode])
        
        if participants != None:
            players = [ {
                "display_name": p["display_name"],
                "is_owner": p["is_owner"],
                "has_submitted": p["has_submitted"]
            } for p in participants ]

            return {
                "players": players,
                "joincode": joincode,
                "state": int(game["state"]) # type: ignore
            }

        return { "error": "lobby doesn't exist" }
