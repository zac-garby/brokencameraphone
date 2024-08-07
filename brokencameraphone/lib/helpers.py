import brokencameraphone.lib.db as db

from flask import session, flash
from flask.helpers import url_for
from werkzeug.utils import redirect

def logged_in(handler):
    def new_handler(*args, **kw):
        if "user_id" not in session:
            return redirect(url_for("index"))
    
        user = db.query(
        """
        select has_confirmed_email
        from users
        where id = ?
        """, [session["user_id"]], one=True)

        if user == None:
            return redirect(url_for("index"))
        
        if user["has_confirmed_email"] == 0: # type: ignore
            return redirect(url_for("index"))

        return handler(*args, **kw)
    
    new_handler.__name__ = "logged_in_handler_" + handler.__name__
    
    return new_handler

def with_participant(param):
    def wrapper(handler):
        def new_handler(*args, **kw):
            participant = db.query("""
                select * from participants
                inner join games on participants.game_id = games.id
                where user_id = ? and games.join_code = ?
                """,
                [session["user_id"], kw["joincode"]], one=True)
            
            kw[param] = participant
            
            return handler(*args, **kw)
        
        new_handler.__name__ = "with_participant_handler_" + handler.__name__
        
        return new_handler
    
    return wrapper

def with_game(param):
    def wrapper(handler):
        def new_handler(*args, **kw):
            game = db.query("""
            select
                games.*,
                case
                    when archived.user_id is not null then 1 else 0
                end as is_archived
            from games
            left join archived on games.id = archived.game_id and archived.user_id = ?
            where join_code = ?
                            """, [session["user_id"], kw["joincode"]], one=True)
            
            if game is None:
                flash(f"The game {kw['joincode']} does not exist.")
                return redirect(url_for("index"))

            kw[param] = game

            return handler(*args, **kw)
        
        new_handler.__name__ = "with_game_handler_" + handler.__name__

        return new_handler

    return wrapper

def lobby_owner(otherwise):
    def wrapper(handler):
        def new_handler(*args, **kw):
            game = db.query("select * from games where join_code = ?",
                                [kw["joincode"]], one=True)
            
            if game is None:
                flash(f"The game {kw['joincode']} does not exist.")
                return redirect(url_for("index"))
            
            if game["owner_id"] != session["user_id"]: # type: ignore
                flash(f"You must be the owner of the game to do this!")
                return redirect(url_for("index"))
            
            return handler(*args, **kw)
        
        new_handler.__name__ = "lobby_owner_handler_" + handler.__name__

        return new_handler
    
    return wrapper