import brokencameraphone.lib.db as db
import brokencameraphone.lib.helpers as helpers
import brokencameraphone.lib.gamemode as gamemode

import random
import re

from brokencameraphone.lib.discord import send_disc_notif
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
    @helpers.with_game("game")
    def leave_game_get(joincode, participant, game):
        if participant is None:
            flash("You attempted to leave a game which you're not in!")
            return redirect(url_for("index"))
        
        if game["state"] != 0:
            flash("You can't leave a game which has started.")
            return redirect(url_for("index"))
        
        if participant["user_id"] == game["owner_id"]:
            flash("You can't leave the game - you made it!")
            return redirect(url_for("index"))
  
        db.query("delete from participants where user_id = ? and game_id = ?",
                [session["user_id"], participant["game_id"]], # type: ignore
                commit=True)
        
        return redirect(url_for("index"))
    
    @app.post("/start-game/<joincode>")
    @helpers.logged_in
    @helpers.with_participant("participant")
    @helpers.lobby_owner(otherwise="index")
    def start_game_get(joincode, participant):
        if participant is None:
            flash("You attempted to start a game which you're not in!", category="error")
            return redirect("/game/" + joincode)
        
        # set max rounds option
        try:
            max_rounds = int(request.form["max_rounds"])
        except Exception:
            flash("Number of rounds wasn't specified.", category="error")
            return redirect("/game/" + joincode)
        
        if max_rounds < 1:
            flash("You need at least one round!", category="error")
            return redirect("/game/" + joincode)

        # get selected gamemode
        form = request.form

        gamemode_str = re.match(
            "gamemode-(\\d+)",
            form.get("gamemode", default="gamemode-0"))
        
        if gamemode_str == None or (gamemode_id := int(gamemode_str[1])) not in gamemode.GAMEMODES:
            flash(f"Invalid gamemode ID provided: {gamemode_id}", category="error")
            return redirect("/game/" + joincode)
        
        the_gamemode = gamemode.GAMEMODES[gamemode_id]
        
        # check that there are enough participants in the lobby to begin
        participants = db.query(
            """
            select * from participants
            inner join games on games.id = participants.game_id
            where games.join_code = ?
            """, [joincode])
        
        if participants == None or len(participants) <= 1:
            flash("You need at least two players to start a game.", category="error")
            return redirect("/game/" + joincode)
        
        # set the gamemode's options from the request form
        for opt in the_gamemode["options"]:
            opt_val = form.get(f"option-{gamemode_id}-{opt['name']}", default="off") == "on"

            db.query(
                f"""
                update games
                set {opt['db_column']} = ?
                where join_code = ?""",
                [opt_val, joincode], commit=True)

        if request.form["webhook_selector"] != "none":
            webhook = request.form["webhook_selector"]
            new_game_desc = f"""
            A new game **{joincode}** has started!

            Click [here](https://whisperingcameraphone.com/game/{joincode}) to start sending those prompts!"""
            send_disc_notif(endpoint=webhook, subject="New game started", desc=new_game_desc, game=joincode)
        else:
            webhook = None

        # set the state, max rounds, gamemode, etc.
        db.query(
            """
            update games
            set state = 1,
            max_rounds = ?,
            current_showing_user = ?,
            gamemode = ?,
            discord_webhook = ?
            where join_code = ?""",
            [max_rounds, session["user_id"], gamemode_id, webhook, joincode], commit=True)
        
        flash("Let the games commence!")

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
        
        db.query("""
                 insert into games (join_code, owner_id, state, current_round, max_rounds)
                 values (?, ?, 0, 0, 0)
                 """,
                [code, session["user_id"]],
                commit=True)
        
        print("making game with code", code)
        return redirect(f"/game/{code}")

    @app.get("/api/lobby/<joincode>")
    @helpers.logged_in
    @helpers.with_game("game")
    def api_lobby(joincode, game):
        participants = db.query("""
        select display_name, users.id as "user_id", users.id = g.owner_id as "is_owner", p.has_submitted from users
        inner join participants as p on users.id = p.user_id
        inner join games as g on p.game_id = g.id
        where g.join_code = ?
                            """,
                            [joincode])
        
        if participants != None:
            players = [ {
                "display_name": p["display_name"],
                "user_id": p["user_id"],
                "is_owner": p["is_owner"],
                "has_submitted": p["has_submitted"]
            } for p in participants ]

            return {
                "players": players,
                "joincode": joincode,
                "state": int(game["state"]) # type: ignore
            }

        return { "error": "lobby doesn't exist" }
