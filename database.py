import sqlite3, os

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "collab.db")

def get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # returns dict-like rows
    return conn

def init_db():
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS rooms (
            room_id      TEXT PRIMARY KEY,
            name         TEXT NOT NULL,
            floor        INTEGER,
            capacity     INTEGER,
            av_tier      TEXT,
            has_camera   INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS meetings (
            meeting_id       TEXT PRIMARY KEY,
            room_id          TEXT REFERENCES rooms(room_id),
            organizer        TEXT,
            subject          TEXT,
            start_time       TEXT,
            end_time         TEXT,
            duration_minutes INTEGER,
            attendees_invited INTEGER,
            attendees_actual  INTEGER,
            is_online        INTEGER DEFAULT 0,
            had_no_show      INTEGER DEFAULT 0,
            day_of_week      TEXT,
            hour_slot        INTEGER
        );

        CREATE TABLE IF NOT EXISTS ai_analysis (
            meeting_id         TEXT PRIMARY KEY,
            summary            TEXT,
            action_items       TEXT,
            sentiment          TEXT,
            effectiveness      INTEGER,
            follow_up_needed   INTEGER
        );
    """)
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized at", DB_PATH)