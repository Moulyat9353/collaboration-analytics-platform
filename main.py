from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from database import get_conn, init_db
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Collab Analytics API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    init_db()

@app.get("/")
def root():
    return {"status": "running", "docs": "/docs"}

@app.get("/api/rooms")
def get_rooms():
    conn = get_conn()
    rooms = conn.execute("SELECT * FROM rooms").fetchall()
    conn.close()
    return [dict(r) for r in rooms]

@app.get("/api/utilization")
def get_utilization(days: int = Query(30, ge=7, le=180)):
    conn = get_conn()
    rows = conn.execute("""
        SELECT
            r.room_id,
            r.name,
            r.floor,
            r.capacity,
            r.av_tier,
            COUNT(m.meeting_id)                          AS total_meetings,
            ROUND(AVG(m.attendees_actual * 1.0), 1)      AS avg_actual,
            ROUND(AVG(m.attendees_invited * 1.0), 1)     AS avg_invited,
            SUM(m.had_no_show)                           AS no_shows,
            ROUND(
                SUM(m.duration_minutes) * 100.0
                / (? * 9 * 60), 1
            )                                            AS utilization_pct,
            ROUND(
                (1.0 - AVG(m.attendees_actual * 1.0)
                     / AVG(m.attendees_invited * 1.0))
                * 100, 1
            )                                            AS capacity_waste_pct
        FROM rooms r
        LEFT JOIN meetings m ON r.room_id = m.room_id
            AND m.start_time >= datetime('now', ? || ' days')
        GROUP BY r.room_id
        ORDER BY utilization_pct DESC
    """, (days, f"-{days}")).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.get("/api/heatmap")
def get_heatmap(days: int = 30):
    conn = get_conn()
    rows = conn.execute("""
        SELECT
            day_of_week,
            hour_slot,
            COUNT(*) AS meeting_count,
            ROUND(AVG(attendees_actual * 1.0), 1) AS avg_attendees
        FROM meetings
        WHERE start_time >= datetime('now', ? || ' days')
        GROUP BY day_of_week, hour_slot
        ORDER BY hour_slot
    """, (f"-{days}",)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.get("/api/capacity-mismatch")
def get_capacity_mismatch():
    conn = get_conn()
    rows = conn.execute("""
        SELECT
            r.name,
            r.capacity,
            ROUND(AVG(m.attendees_actual * 1.0), 1) AS avg_actual,
            ROUND(
                (1.0 - AVG(m.attendees_actual * 1.0) / r.capacity)
                * 100, 1
            ) AS waste_pct
        FROM rooms r
        JOIN meetings m ON r.room_id = m.room_id
        WHERE m.start_time >= datetime('now', '-30 days')
        GROUP BY r.room_id
        HAVING r.capacity >= 10
        ORDER BY waste_pct DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.get("/api/trends")
def get_trends():
    conn = get_conn()
    rows = conn.execute("""
        SELECT
            strftime('%Y-%W', start_time) AS week,
            COUNT(*)                       AS total_meetings,
            ROUND(AVG(attendees_actual * 1.0), 1) AS avg_attendees,
            SUM(had_no_show)               AS no_shows,
            SUM(is_online)                 AS online_meetings
        FROM meetings
        WHERE start_time >= datetime('now', '-90 days')
        GROUP BY week
        ORDER BY week
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.get("/api/summary")
def get_summary():
    conn = get_conn()
    row = conn.execute("""
        SELECT
            COUNT(*)                             AS total_meetings,
            ROUND(AVG(attendees_actual * 1.0),1) AS avg_attendees,
            SUM(had_no_show)                     AS total_no_shows,
            SUM(is_online)                       AS online_meetings,
            COUNT(DISTINCT room_id)              AS active_rooms
        FROM meetings
        WHERE start_time >= datetime('now', '-30 days')
    """).fetchone()
    conn.close()
    return dict(row)