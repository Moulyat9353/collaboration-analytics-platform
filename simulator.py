import sqlite3, uuid, random
from datetime import datetime, timedelta
from faker import Faker
from database import get_conn, init_db

fake = Faker()

ROOMS = [
    ("R001", "Everest",     5, 20, "basic",           0),
    ("R002", "Olympus",     5, 16, "basic",           0),
    ("R003", "Denali",      4, 12, "teams_certified", 1),
    ("R004", "Fuji",        4, 10, "teams_certified", 1),
    ("R005", "Atlas",       4, 14, "basic",           0),
    ("R006", "Kilimanjaro", 3,  8, "basic",           0),
    ("R007", "Base Camp",   3,  6, "none",            0),
    ("R008", "Summit",      3,  4, "none",            0),
]

SUBJECTS = [
    "Q{q} Planning", "Sprint Retrospective", "1:1 Sync",
    "All Hands Engineering", "Customer Discovery",
    "Design Review", "Budget Review", "Roadmap Planning",
    "Incident Post-Mortem", "Architecture Review",
]

def simulate(days_back=180, meetings_per_day=25):
    init_db()
    conn = get_conn()

    # Insert rooms
    conn.executemany(
        "INSERT OR REPLACE INTO rooms VALUES (?,?,?,?,?,?)", ROOMS
    )

    meetings = []
    for day_offset in range(days_back):
        date = datetime.now() - timedelta(days=day_offset)

        # Skip weekends
        if date.weekday() >= 5:
            continue

        # More meetings on Tue/Wed/Thu
        day_count = int(meetings_per_day * {
            0: 0.7, 1: 1.2, 2: 1.3, 3: 1.1, 4: 0.7
        }[date.weekday()])

        for _ in range(day_count):
            room = random.choice(ROOMS)
            room_id, _, _, capacity, _, _ = room

            # Peak hours bias
            hour = random.choices(
                range(8, 18),
                weights=[2, 5, 10, 10, 7, 4, 8, 10, 8, 4]
            )[0]
            minute = random.choice([0, 30])
            start = date.replace(hour=hour, minute=minute, second=0, microsecond=0)
            duration = random.choice([30, 60, 90, 120])
            end = start + timedelta(minutes=duration)

            # Invited vs actual — large rooms tend to be underused
            invited = random.randint(2, min(capacity, 15))
            # Big rooms have more waste
            waste_factor = 0.4 if capacity >= 12 else 0.75
            actual = max(1, int(invited * random.uniform(waste_factor, 1.0)))

            no_show = 1 if actual < invited * 0.6 else 0
            quarter = (start.month - 1) // 3 + 1

            meetings.append((
                str(uuid.uuid4()),
                room_id,
                fake.name(),
                random.choice(SUBJECTS).format(q=quarter),
                start.isoformat(),
                end.isoformat(),
                duration,
                invited,
                actual,
                1 if random.random() > 0.4 else 0,
                no_show,
                start.strftime("%A"),
                hour
            ))

    conn.executemany("""
        INSERT OR IGNORE INTO meetings VALUES
        (?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, meetings)

    conn.commit()
    conn.close()
    print(f"Inserted {len(meetings)} meetings across {days_back} days")

if __name__ == "__main__":
    simulate()