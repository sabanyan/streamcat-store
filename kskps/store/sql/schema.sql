CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(256) NOT NULL,
    password CHAR(64) NOT NULL,
    name VARCHAR(64) NOT NULL DEFAULT '',
    created_at TIMESTAMP DEFAULT (DATETIME('now','localtime')),
    modified_at TIMESTAMP DEFAULT (DATETIME('now','localtime')),
    creator VARCHAR(256) NOT NULL DEFAULT '',
    modifier VARCHAR(256) NOT NULL DEFAULT ''
);

CREATE TABLE projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uuid CHAR(36) NOT NULL DEFAULT '',
    name VARCHAR(256) NOT NULL DEFAULT '',
    creator_id INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT (DATETIME('now','localtime')),
    modified_at TIMESTAMP DEFAULT (DATETIME('now','localtime')),
    creator VARCHAR(256) NOT NULL DEFAULT '',
    modifier VARCHAR(256) NOT NULL DEFAULT ''
);

CREATE TABLE users_x_projects (
    user_id INTEGER NOT NULL,
    project_id INTEGER NOT NULL
);

