import os
import lib.db as db
import lib.helpers as helpers

from flask import Flask, session, request, flash
from flask.helpers import url_for
from flask.templating import render_template
from werkzeug.utils import redirect

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "bmp"}

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
        
        if all_submitted(joincode):
            advance_round(joincode, game)

        return redirect("/game/" + joincode)
    
    @app.post("/submit-photo/<joincode>")
    @helpers.logged_in
    @helpers.with_game("game")
    @helpers.with_participant("participant")
    def submit_photo_post(joincode, participant, game):
        if game["state"] != 2:
            flash("You can't submit a photo in this game state!")
            return redirect("/game/" + joincode)
        
        if participant["has_submitted"] > 0:
            flash("You already submitted for this round!")
            return redirect("/game/" + joincode)
        
        # submit the photo
        if "photo" not in request.files or request.files["photo"].filename == "":
            flash("No photo uploaded...")
            return redirect("/game/" + joincode)
        
        photo = request.files["photo"]
        allowed, ext = allowed_photo_file(photo.filename)

        if photo and allowed:
            new_filename = f"photo_{joincode}_{participant['user_id']}_{game['current_round']}.{ext}"
            path = os.path.join(app.config["UPLOAD_FOLDER"], new_filename)
            photo.save(path)
        else:
            flash("This file format is not supported. Please use either PNG, JPEG, BMP, or GIF!")
            return redirect("/game/" + joincode)
        
        # submit the photo
        db.query("""
                 insert into submissions (user_id, game_id, round, photo_path)
                 values (?, ?, ?, ?)
                 """,
                 [session["user_id"], game["id"], game["current_round"], path],
                 commit=True)
        
        # record that the participant has submitted for this game
        db.query("""
                 update participants
                 set has_submitted = 1
                 where user_id = ? and game_id = ?
                 """,
                 [session["user_id"], game["id"]],
                 commit=True)
        
        if all_submitted(joincode):
            advance_round(joincode, game)

        return redirect("/game/" + joincode)

def allowed_photo_file(filename):
    ext = filename.rsplit(".", 1)[1].lower()
    return ("." in filename and ext in ALLOWED_EXTENSIONS), ext

def all_submitted(joincode):
    not_submitted = db.query(
        """
        select * from participants
        inner join games on participants.game_id = games.id
        where join_code = ? and has_submitted = 0
        """,
        [joincode])
    
    return not_submitted == None or len(not_submitted) == 0

def advance_round(joincode, game):
    db.query(
        """
        update participants
        set has_submitted = 0
        """, commit=True)
    
    # if prompts, go to photos. otherwise, go to prompts
    new_state = 2 if game["state"] in [1, 3] else 3
    
    db.query(
        """
        update games
        set current_round = current_round + 1,
            state = ?
        where join_code = ?
        """, [new_state, joincode], commit=True)
