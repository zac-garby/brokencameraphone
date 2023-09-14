import lib.db as db
import lib.helpers as helpers

from flask import Flask, session, request, flash
from flask.helpers import url_for
from flask.templating import render_template
from werkzeug.utils import redirect

def register_routes(app: Flask):
    @app.post("/submit-prompt/<joincode>")
    @helpers.logged_in
    @helpers.with_game("game")
    @helpers.with_participant("participant")
    def submit_prompt_post(joincode, participant, game):
        if game["state"] not in [1, 3]:
            flash("You can't submit a prompt in this game state!")
            return redirect("/game/" + joincode)
        
        if participant["has_submitted"] > 0:
            flash("You already submitted for this round!")
            return redirect("/game/" + joincode)
        
        # submit the prompt
        db.query("""
                 insert into submissions (user_id, game_id, round, prompt)
                 values (?, ?, ?, ?)
                 """,
                 [session["user_id"], game["id"], game["current_round"], request.form["prompt"]],
                 commit=True)
        
        # record that the participant has submitted for this game
        db.query("""
                 update participants
                 set has_submitted = 1
                 where user_id = ? and game_id = ?
                 """,
                 [session["user_id"], game["id"]],
                 commit=True)

        return redirect("/game/" + joincode)