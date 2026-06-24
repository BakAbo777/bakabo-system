-- BKS VERSE — SQLite Schema v1
PRAGMA foreign_keys = ON;

-- ── POET ARCHIVE ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS poet_archive (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    slug            TEXT UNIQUE NOT NULL,         -- 'celan', 'ungaretti'
    name            TEXT NOT NULL,
    country_code    TEXT NOT NULL,                -- 'DE', 'IT', 'US'
    era             TEXT NOT NULL,                -- '1920-1970'
    city            TEXT,                         -- 'Parigi'
    year_birth      INTEGER,
    year_death      INTEGER,
    rep_poem_title  TEXT,                         -- titolo poesia rappresentativa
    rep_poem_excerpt TEXT,                        -- estratto (max 280 char)
    rep_poem_lang   TEXT DEFAULT 'it',
    score_image     INTEGER CHECK(score_image BETWEEN 1 AND 5),
    score_voice     INTEGER CHECK(score_voice BETWEEN 1 AND 5),
    score_tension   INTEGER CHECK(score_tension BETWEEN 1 AND 5),
    score_bks       INTEGER CHECK(score_bks BETWEEN 1 AND 5),
    score_body      INTEGER CHECK(score_body BETWEEN 1 AND 5),
    score_total     INTEGER GENERATED ALWAYS AS
                    (score_image + score_voice + score_tension + score_bks + score_body) STORED,
    photo_url       TEXT,
    bio_short       TEXT,
    created_at      TEXT DEFAULT (datetime('now'))
);

-- ── VERSE SUBMISSIONS ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS verse_submissions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    member_email    TEXT NOT NULL,
    member_id       TEXT,                         -- Shopify customer ID
    member_display  TEXT,                         -- nome pubblico (opt-in)
    member_tier     TEXT DEFAULT 'brass',         -- brass/silver/gold
    collection_slug TEXT,                         -- 'bks-hours', 'bks-glyph'...
    poem_text       TEXT NOT NULL,
    poem_lang       TEXT DEFAULT 'it',
    char_count      INTEGER,
    submitted_at    TEXT DEFAULT (datetime('now')),
    -- Giudice scoring
    score_image     INTEGER,
    score_voice     INTEGER,
    score_tension   INTEGER,
    score_bks       INTEGER,
    score_body      INTEGER,
    score_total     INTEGER,
    giudice_notes   TEXT,                         -- JSON: {axis: comment}
    giudice_verdict TEXT,                         -- 'approved'|'rejected'|'pending'
    scored_at       TEXT,
    -- Anti-spam
    gptzero_score   REAL,                         -- 0.0-1.0 (1.0 = human)
    spam_flagged    INTEGER DEFAULT 0,
    -- Lineage
    ancestor_poet_id INTEGER REFERENCES poet_archive(id),
    lineage_note    TEXT,                         -- why this poet is the ancestor
    -- Status
    status          TEXT DEFAULT 'pending',       -- pending|approved|rejected|hall
    product_created INTEGER DEFAULT 0,
    product_id      TEXT,                         -- Shopify product ID if created
    reel_generated  INTEGER DEFAULT 0,
    reel_url        TEXT,
    -- Make.com trigger
    make_triggered  INTEGER DEFAULT 0,
    make_response   TEXT
);

-- ── MEMBER POET SCORE ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS member_poet_score (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    member_email    TEXT UNIQUE NOT NULL,
    member_id       TEXT,
    -- Behavioral signals
    collections_bought TEXT,                      -- JSON array of collection slugs
    editorial_views INTEGER DEFAULT 0,
    ai_chat_turns   INTEGER DEFAULT 0,
    submissions_total INTEGER DEFAULT 0,
    submissions_approved INTEGER DEFAULT 0,
    best_score      INTEGER DEFAULT 0,
    -- Computed Poet Score (0-100)
    poet_score      REAL DEFAULT 0.0,
    tier_unlocked   TEXT DEFAULT 'none',          -- 'none'|'apprentice'|'voice'|'master'
    updated_at      TEXT DEFAULT (datetime('now'))
);

-- ── VERSE HALL OF FAME ────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS verse_hall (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    submission_id   INTEGER REFERENCES verse_submissions(id),
    member_email    TEXT NOT NULL,
    member_display  TEXT,                         -- how they want to appear
    poem_text       TEXT NOT NULL,
    score_total     INTEGER NOT NULL,
    ancestor_poet_slug TEXT,
    inducted_at     TEXT DEFAULT (datetime('now')),
    product_url     TEXT,
    limited_edition_num INTEGER
);

-- ── REEL QUEUE ────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS reel_queue (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    submission_id   INTEGER REFERENCES verse_submissions(id),
    poet_slug       TEXT REFERENCES poet_archive(slug),
    reel_type       TEXT DEFAULT 'lineage',       -- 'lineage'|'hall'|'episode'
    storyboard_json TEXT,
    status          TEXT DEFAULT 'queued',        -- queued|generating|done|failed
    heygen_job_id   TEXT,
    output_url      TEXT,
    created_at      TEXT DEFAULT (datetime('now')),
    completed_at    TEXT
);

-- ── INDEXES ──────────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_submissions_member ON verse_submissions(member_email);
CREATE INDEX IF NOT EXISTS idx_submissions_status ON verse_submissions(status);
CREATE INDEX IF NOT EXISTS idx_submissions_score  ON verse_submissions(score_total DESC);
CREATE INDEX IF NOT EXISTS idx_hall_score         ON verse_hall(score_total DESC);
