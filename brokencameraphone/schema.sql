DROP TABLE IF EXISTS users;
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    display_name TEXT NOT NULL,
    password CHAR(60) NOT NULL,
    has_confirmed_email INTEGER NOT NULL,
    email_confirmation_code TEXT NOT NULL
);

DROP TABLE IF EXISTS games;
CREATE TABLE games (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    join_code TEXT COLLATE NOCASE,
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

DROP TABLE IF EXISTS chain_links;
CREATE TABLE chain_links (
    -- the chain link specifies the prompt which to_id receives
    -- when games.current_round = round.
    -- the prompt is taken from from_id's submission from the
    -- previous round (round - 1).

    game_id INTEGER NOT NULL,
    round INTEGER NOT NULL,

    from_id INTEGER NOT NULL,
    to_id INTEGER NOT NULL,

    FOREIGN KEY (game_id) REFERENCES games (id),
    FOREIGN KEY (from_id) REFERENCES users (id),
    FOREIGN KEY (to_id) REFERENCES users (id),

    PRIMARY KEY (game_id, round, from_id, to_id)
);

DROP TABLE IF EXISTS archived;
CREATE TABLE archived (
    user_id INTEGER NOT NULL,
    game_id INTEGER NOT NULL,

    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (game_id) REFERENCES games (id),

    PRIMARY KEY (user_id, game_id)
);