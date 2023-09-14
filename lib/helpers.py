import lib.db as db

from flask import session
from flask.helpers import url_for
from werkzeug.utils import redirect

def logged_in(handler):
    def new_handler(*args, **kw):
        if "user_id" not in session:
            return redirect(url_for("index"))

        return handler(*args, **kw)
    
    new_handler.__name__ = "logged_in_handler_" + handler.__name__
    
    return new_handler

def with_participant(handler):
    def new_handler(*args, **kw):
        participant = db.query("""
            select * from participants
            inner join games on participants.game_id = games.id
            where user_id = ? and games.join_code = ?
            """,
            [session["user_id"], kw["joincode"]], one=True)
        
        kw["participant"] = participant
        
        return handler(*args, **kw)
    
    new_handler.__name__ = "with_participant_handler_" + handler.__name__
    
    return new_handler