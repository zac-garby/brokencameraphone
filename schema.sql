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

    -- 0: in lobby
    -- 1: doing initial prompts
    -- 2: doing photos
    -- 3: doing prompts from photos
    state INTEGER,

    FOREIGN KEY (owner_id) REFERENCES user (id)
);

DROP TABLE IF EXISTS participants;
CREATE TABLE participants (
    user_id INTEGER NOT NULL,
    game_id INTEGER NOT NULL,

    FOREIGN KEY (user_id) REFERENCES user (id),
    FOREIGN KEY (game_id) REFERENCES game (id),

    PRIMARY KEY (user_id, game_id)
);