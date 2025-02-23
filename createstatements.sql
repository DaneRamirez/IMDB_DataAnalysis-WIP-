--Used for Postgresql Database.--
--Only use this SQL script to create tables required--

-- Table: title_akas
CREATE TABLE title_akas (
    titleId TEXT NOT NULL,
    ordering INTEGER NOT NULL,
    title TEXT NOT NULL,
    region TEXT,
    language TEXT,
    types TEXT[],  -- Array of alternative title types
    attributes TEXT[],  -- Array of additional attributes
    isOriginalTitle BOOLEAN NOT NULL,
    PRIMARY KEY (titleId, ordering),
    FOREIGN KEY (titleId) REFERENCES title_basics(tconst) ON DELETE CASCADE
);

-- Table: title_basics
CREATE TABLE title_basics (
    tconst TEXT PRIMARY KEY,
    titleType TEXT NOT NULL,
    primaryTitle TEXT NOT NULL,
    originalTitle TEXT NOT NULL,
    isAdult BOOLEAN NOT NULL,
    startYear INTEGER,
    endYear INTEGER,
    runtimeMinutes INTEGER,
    genres TEXT[] -- Array of up to three genres
);

-- Table: title_crew
CREATE TABLE title_crew (
    tconst TEXT PRIMARY KEY,
    directors TEXT[],  -- Array of nconsts (directors)
    writers TEXT[],  -- Array of nconsts (writers)
    FOREIGN KEY (tconst) REFERENCES title_basics(tconst) ON DELETE CASCADE
);

-- Table: title_episode
CREATE TABLE title_episode (
    tconst TEXT PRIMARY KEY,
    parentTconst TEXT NOT NULL,
    seasonNumber INTEGER,
    episodeNumber INTEGER,
    FOREIGN KEY (parentTconst) REFERENCES title_basics(tconst) ON DELETE CASCADE
);

-- Table: title_principals
CREATE TABLE title_principals (
    tconst TEXT NOT NULL,
    ordering INTEGER NOT NULL,
    nconst TEXT NOT NULL,
    category TEXT NOT NULL,
    job TEXT,
    characters TEXT,
    PRIMARY KEY (tconst, ordering, nconst),
    FOREIGN KEY (tconst) REFERENCES title_basics(tconst) ON DELETE CASCADE,
    FOREIGN KEY (nconst) REFERENCES name_basics(nconst) ON DELETE CASCADE
);

-- Table: title_ratings
CREATE TABLE title_ratings (
    tconst TEXT PRIMARY KEY,
    averageRating DECIMAL(3,1) NOT NULL,
    numVotes INTEGER NOT NULL,
    FOREIGN KEY (tconst) REFERENCES title_basics(tconst) ON DELETE CASCADE
);

-- Table: name_basics
CREATE TABLE name_basics (
    nconst TEXT PRIMARY KEY,
    primaryName TEXT NOT NULL,
    birthYear INTEGER,
    deathYear INTEGER,
    primaryProfession TEXT[],  -- Array of professions
    knownForTitles TEXT[] -- Array of tconsts
);
