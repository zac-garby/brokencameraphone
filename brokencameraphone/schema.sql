DROP TABLE IF EXISTS users;
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    display_name TEXT NOT NULL,
    password CHAR(60) NOT NULL
);

DROP TABLE IF EXISTS games;
CREATE TABLE games (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    join_code TEXT,
    owner_id INTEGER NOT NULL,

    current_round INTEGER NOT NULL,
    max_rounds INTEGER NOT NULL,

    current_showing_user INTEGER DEFAULT 0 NOT NULL,

    -- 0: in lobby
    -- 1: doing initial prompts
    -- 2: doing photos
    -- 3: doing prompts from photos
    -- 4: game finished
    state INTEGER,

    FOREIGN KEY (owner_id) REFERENCES users (id),
    FOREIGN KEY (current_showing_user) REFERENCES users (id)
);

DROP TABLE IF EXISTS participants;
CREATE TABLE participants (
    user_id INTEGER NOT NULL,
    game_id INTEGER NOT NULL,

    ordering INTEGER NOT NULL,
    has_submitted INTEGER NOT NULL,

    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (game_id) REFERENCES games (id),

    PRIMARY KEY (user_id, game_id)
);

DROP TABLE IF EXISTS submissions;
CREATE TABLE submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    user_id INTEGER NOT NULL,
    game_id INTEGER NOT NULL,

    -- the round which this submission was from.
    round INTEGER NOT NULL,

    -- the id of the user from whom this submission
    -- is originally based.
    root_user INTEGER NOT NULL,

    -- whether this submission has been revealed yet
    -- in the post-game gallery thing.
    revealed INTEGER DEFAULT 0 NOT NULL,

    -- either photo_path or prompt is NULL, depending
    -- on whether this round was a photo or prompt round.
    photo_path TEXT,
    prompt TEXT,

    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (game_id) REFERENCES games (id),
    FOREIGN KEY (root_user) REFERENCES users (id)
);