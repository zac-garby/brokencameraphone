import os
import random
import brokencameraphone.lib.db as db
import brokencameraphone.lib.helpers as helpers
import zipfile
import tempfile
import io

from PIL import Image
from io import BytesIO
from slugify import slugify

from flask import Flask, session, request, flash, send_from_directory, abort, send_file
from flask.helpers import url_for
from flask.templating import render_template
from werkzeug.utils import redirect

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "bmp"}
MAX_IMAGE_SIZE = (2048, 2048)
MAX_IMAGE_KB = 256

def register_routes(app: Flask):
    @app.get("/game/<joincode>")
    @helpers.logged_in
    @helpers.with_game("game")
    @helpers.with_participant("participant")
    def game_get(joincode, game, participant):
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
                db.query("""
                         insert into participants (user_id, game_id, has_submitted, ordering)
                         values (?, ?, 0, (select count(*) from participants where game_id = ?))
                         """,
                    [session["user_id"], game["id"], game["id"]], # type: ignore
                    commit=True)
                return redirect("/game/" + joincode)
        
        # rejoining a game which the user is already part of
        else:
            template = {
                0: "lobby.html",
                1: "initial-prompt.html",
                2: "photo.html",
                3: "photo-prompt.html",
                4: "game-over.html"
            }[state]

            return render_template(
                template,
                game=game,
                participant=participant,
                previous_submission=get_previous_submission(joincode, participant),
                recent_submission=get_recent_submission(joincode, participant),
                user_id=session["user_id"],
                is_owner=game['owner_id'] == session["user_id"]) # type: ignore
        
    @app.post("/submit-prompt/<joincode>")
    @helpers.logged_in
    @helpers.with_game("game")
    @helpers.with_participant("participant")
    def submit_prompt_post(joincode, participant, game):
        if game["state"] not in [1, 3]:
            flash("You can't submit a prompt in this game state!")
            return redirect("/game/" + joincode)
        
        if len(request.form["prompt"]) == 0:
            flash("Your prompt can't be empty.")
            return redirect("/game/" + joincode)
        
        if participant["has_submitted"] > 0:
            flash("You already submitted for this round!")
            return redirect("/game/" + joincode)
        
        prev = get_previous_submission(joincode, participant)
        if prev == None:
            prev = {"root_user": session["user_id"]}
        
        # submit the prompt
        db.query("""
                 insert into submissions (user_id, game_id, round, prompt, root_user)
                 values (?, ?, ?, ?, ?)
                 """,
                 [
                     session["user_id"],
                     game["id"],
                     game["current_round"],
                     request.form["prompt"],
                     prev["root_user"] # type: ignore
                 ],
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
        
        prev = get_previous_submission(joincode, participant)
        if prev == None:
            prev = {"root_user": session["user_id"]}
        
        # submit the photo
        if "photo" not in request.files or request.files["photo"].filename == "":
            flash("No photo uploaded...")
            return redirect("/game/" + joincode)
        
        photo = request.files["photo"]
        allowed, ext = allowed_photo_file(photo.filename)

        if photo and allowed:
            new_filename = f"photo_{joincode}_{participant['user_id']}_{game['current_round']}.{ext}"
            path = os.path.join(app.config["UPLOAD_FOLDER"], new_filename)
            compress_image_to_size(photo, path, target_size_kb=MAX_IMAGE_KB)
        else:
            flash("This file format is not supported. Please use either PNG, JPEG, BMP, or GIF!")
            return redirect("/game/" + joincode)
        
        # submit the photo
        db.query("""
                 insert into submissions (user_id, game_id, round, photo_path, root_user)
                 values (?, ?, ?, ?, ?)
                 """,
                 [
                     session["user_id"],
                     game["id"],
                     game["current_round"],
                     new_filename,
                     prev["root_user"] # type: ignore
                 ],
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
    
    @app.get("/photo/<path>")
    def get_photo(path):
        return send_from_directory(app.config["UPLOAD_FOLDER"], path)
    
    @app.get("/api/game/<joincode>")
    @helpers.logged_in
    def get_api_games_info(joincode):
        game = db.query(
            """
            select * from games
            where join_code = ?
            """, [joincode], one=True)
        
        if game == None:
            return {
                "exists": False,
                "info": None
            }

        return {
            "exists": True,
            "info": {
                "join_code": game["join_code"], # type: ignore
                "current_round": game["current_round"], # type: ignore
                "max_rounds": game["max_rounds"], # type: ignore
                "current_showing_user": game["current_showing_user"], # type: ignore
                "state": game["state"] # type: ignore
            }
        }
    
    @app.get("/api/gallery/view/<joincode>")
    @helpers.logged_in
    @helpers.with_game("game")
    @helpers.with_participant("participant")
    def get_api_gallery_view(joincode, game, participant):
        submissions = db.query(
            """
            select round, photo_path, prompt, display_name, root_user from submissions
            inner join games on games.id = submissions.game_id
            inner join users on users.id = submissions.user_id
            where games.current_showing_user = submissions.root_user and submissions.revealed and games.join_code = ?
            order by round desc
            """, [joincode])
        
        if submissions == None or len(submissions) == 0:
            return {
                "submissions": [],
                "amount": 0,
                "current_showing_user": game["current_showing_user"]
            }
        
        return {
            "submissions": [ {
                "round": s["round"],
                "photo_path": s["photo_path"],
                "prompt": s["prompt"],
                "display_name": s["display_name"]
            } for s in submissions ],
            "current_showing_user": game["current_showing_user"],
            "amount": len(submissions)
        }
    
    @app.get("/api/gallery/set/<joincode>/<user_id>")
    @helpers.logged_in
    @helpers.with_game("game")
    @helpers.with_participant("participant")
    def get_api_gallery_set(joincode, user_id, game, participant):
        db.query(
            """
            update games 
            set current_showing_user = ?
            where join_code = ?
            """, [user_id, joincode], commit=True)
        
        return {
            "ok": True
        }
    
    @app.get("/api/gallery/advance/<joincode>")
    @helpers.logged_in
    @helpers.with_game("game")
    @helpers.with_participant("participant")
    def get_api_gallery_advance(joincode, game, participant):
        if game['owner_id'] != session["user_id"]:
            return {
                "ok": False
            }
        
        db.query("""
                 update submissions
                 set revealed = 1
                 where id = (
                     select submissions.id from submissions
                     inner join games on games.id = game_id
                     where revealed = 0 and root_user = ? and games.join_code = ?
                     order by round asc
                     limit 1
                 )
                 """, [game["current_showing_user"], joincode], commit=True)
        
        return {
            "ok": True
        }
    
    @app.get("/api/gallery/download/<joincode>")
    @helpers.logged_in
    @helpers.with_game("game")
    @helpers.with_participant("participant")
    def get_api_gallery_download(joincode, game, participant):
        if game["state"] != 4:
            flash("You can't download the gallery until the game has finished!")
            return redirect("/game/" + joincode)

        file_name = f"WCP-gallery-{joincode}.zip"
        mem_file = BytesIO()

        chains = get_chains(game["id"])
        if chains == None:
            flash("Invalid game ID")
            return redirect("/game/" + joincode)

        with zipfile.ZipFile(mem_file, "w", zipfile.ZIP_DEFLATED) as f:
            for root_user, chain in chains.items():
                root_name = slugify(user_display_name(root_user)) # type: ignore

                for sub in chain:
                    path_start = os.path.join(
                        root_name,
                        f"{sub['round']}-{slugify(sub['user_name'])}")

                    if sub["photo_path"] is not None:
                        # got a photo; write it directly
                        _, ext = allowed_photo_file(sub["photo_path"])

                        f.write(
                            os.path.join(app.config["UPLOAD_FOLDER"], sub["photo_path"]),
                            arcname=f"{path_start}-photo.{ext}")
                    else:
                        # got a prompt; make a text file to put it in
                        f.writestr(f"{path_start}-prompt.txt", sub["prompt"])

        mem_file.seek(0)

        return send_file(mem_file, download_name=file_name, as_attachment=True)

    @app.get("/set-archived/<joincode>/<val>")
    @helpers.logged_in
    @helpers.with_game("game")
    def get_api_set_archived(joincode, val, game):
        print(joincode, val, game["is_archived"])
        if val == "true" and not game["is_archived"]:
            db.query("""
            insert into archived (user_id, game_id)
            values (?, ?)
                     """, [session["user_id"], game["id"]], commit=True)
        elif val == "false" and game["is_archived"]:
            db.query("""
            delete from archived
            where user_id = ? and game_id = ?
                     """, [session["user_id"], game["id"]], commit=True)
        
        return redirect("/")

def get_chains(game_id):
    all_submissions = db.query(
        """
        select submissions.*, users.display_name as "user_name" from submissions
        inner join users on submissions.user_id = users.id
        where game_id = ?
        """, [game_id])

    if all_submissions == None:
        return None
    
    chains = {}

    for sub in all_submissions:
        if sub["root_user"] not in chains:
            chains[sub["root_user"]] = []
        
        chains[sub["root_user"]].append(sub)
    
    return chains

def user_display_name(user_id):
    name = db.query(
        """
        select display_name
        from users
        where id = ?
        """, [user_id], one=True)

    if name == None:
        return None

    return name["display_name"] # type: ignore

def compress_image_to_size(input_path, output_path, target_size_kb=96):
    target_size_bytes = target_size_kb * 1024
    quality = 95  # Starting quality for compression

    with Image.open(input_path) as img:
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        
        img.thumbnail(MAX_IMAGE_SIZE)

        while True:
            img_io = io.BytesIO()
            img.save(img_io, format='JPEG', quality=quality)
            img_size = img_io.tell()

            if img_size <= target_size_bytes:
                break

            quality -= 5
            if quality < 5:
                # image is too big; give up! :)
                break

    with open(output_path, 'wb') as f:
        f.write(img_io.getvalue())

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
        where game_id = ?
        """, [game["id"]], commit=True)
    
    if game["current_round"] > 2 * game["max_rounds"] - 2:
        # if exceeded max round, game is over
        new_state = 4

        # also, reveal the first prompt of each thread
        db.query(
            """
            update submissions
            set revealed = 1
            where round = 0 and game_id = ?
            """, [game["id"]], commit=True)
    elif game["state"] in [1, 3]:
        # if was doing prompts, change to photos
        assign_chain_links(joincode, game["current_round"] + 1, game["id"])
        new_state = 2
    else:
        # otherwise, change to prompts
        assign_chain_links(joincode, game["current_round"] + 1, game["id"])
        new_state = 3
    
    db.query(
        """
        update games
        set current_round = current_round + 1,
            state = ?
        where join_code = ?
        """, [new_state, joincode], commit=True)

def assign_chain_links(joincode, round_num, game_id):
    froms = db.query("""
    select user_id from participants as p
    inner join games on p.game_id = games.id
    where games.join_code = ?
    """, [joincode])

    user_ids = list(map(lambda row: row["user_id"], froms)) # type: ignore
    user_ids_orig = list(map(lambda row: row["user_id"], froms)) # type: ignore
    print(user_ids)

    while True:
        random.shuffle(user_ids)
        print(user_ids)
        in_place = False
        old_place = False

        # check if any prompts go back to the same player (in_place)
        for (f, t) in zip(user_ids_orig, user_ids):
            if f == t:
                in_place = True
                break
        
        # check if any prompts from two players back go to the same player (old_place)
        if len(user_ids) > 2:
            for (f, t) in zip(user_ids_orig, user_ids):
                f2 = db.query("""
                select from_id from chain_links
                where game_id = ? and round = ? and to_id = ?
                """, [game_id, round_num - 1, f], one=True)

                if f2 != None and int(f2["from_id"]) == t: # type: ignore
                    old_place = True
                    break
        
        if not in_place and not old_place:
            break
    
    for (f, t) in zip(user_ids_orig, user_ids):
        print(f"from {f} to {t}")

        db.query("""
        insert into chain_links (game_id, round, from_id, to_id)
        values (?, ?, ?, ?)
        """, [game_id, round_num, f, t], commit=True)

# gets the prompt (or photo prompt) which a player should be
# prompted with in the current round.
def get_previous_submission(joincode, participant):
    submission = db.query("""
    select s.user_id, s.game_id, s.round, photo_path, prompt, root_user
    from submissions as s
	inner join participants as p on p.user_id = s.user_id
    inner join games as g on s.game_id = g.id
    inner join chain_links as l on l.round = g.current_round and l.to_id = ? and l.from_id = s.user_id and l.game_id = g.id
    where g.join_code = ? and s.round = (g.current_round - 1)
    """, [participant["user_id"], joincode], one=True)

    return submission

# gets the prompt (or photo prompt) which a player recently submitted themselves 
def get_recent_submission(joincode, participant):
    submission = db.query(
        """
        select * from submissions
        inner join games on game_id = games.id
        where games.join_code = ?
            and user_id = ?
            and round = games.current_round
        """, [joincode, participant["user_id"]], one=True)

    return submission