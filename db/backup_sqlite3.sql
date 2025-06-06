BEGIN TRANSACTION;

CREATE TABLE users (
    id INT PRIMARY KEY IDENTITY(1,1),
    username NVARCHAR(255) NOT NULL UNIQUE,
    password_hash NVARCHAR(255) NOT NULL
);

CREATE TABLE consoles (
    id INT PRIMARY KEY IDENTITY(1,1),
    name NVARCHAR(255) NOT NULL,
    model NVARCHAR(255) NOT NULL,
    model_normalized NVARCHAR(255),
    release_date INT,
    manufacturer NVARCHAR(255) NOT NULL,
    serial_number_box NVARCHAR(255),
    serial_number_console NVARCHAR(255),
    complete_in_box BIT,
    condition NVARCHAR(255),
    inventory INT,
    sealed INT
);

CREATE TABLE games (
    id INT PRIMARY KEY IDENTITY(1,1),
    title NVARCHAR(255) NOT NULL,
    release_date INT,
    manufacturer NVARCHAR(255) NOT NULL,
    description NVARCHAR(MAX),
    genre NVARCHAR(255),
    platform NVARCHAR(255),
    platform_normalized NVARCHAR(255),
    score INT,
    complete_in_box BIT,
    condition NVARCHAR(255),
    inventory INT,
    sealed INT
);

CREATE INDEX idx_games_platform ON games(platform);
CREATE INDEX idx_consoles_model ON consoles(model);

COMMIT;

