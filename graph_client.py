import os, httpx
from simulator import simulate

USE_REAL_GRAPH = os.getenv("USE_REAL_GRAPH", "false").lower() == "true"

GRAPH_CONFIG = {
    "tenant_id":     os.getenv("AZURE_TENANT_ID", ""),
    "client_id":     os.getenv("AZURE_CLIENT_ID", ""),
    "client_secret": os.getenv("AZURE_CLIENT_SECRET", ""),
}

async def get_token():
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"https://login.microsoftonline.com/{GRAPH_CONFIG['tenant_id']}/oauth2/v2.0/token",
            data={
                "grant_type":    "client_credentials",
                "client_id":     GRAPH_CONFIG["client_id"],
                "client_secret": GRAPH_CONFIG["client_secret"],
                "scope":         "https://graph.microsoft.com/.default",
            }
        )
        return resp.json()["access_token"]

async def get_rooms():
    if not USE_REAL_GRAPH:
        # Returns simulated rooms from DB
        from database import get_conn
        conn = get_conn()
        rooms = conn.execute("SELECT * FROM rooms").fetchall()
        conn.close()
        return [dict(r) for r in rooms]

    token = await get_token()
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://graph.microsoft.com/v1.0/places/microsoft.graph.room",
            headers={"Authorization": f"Bearer {token}"}
        )
        return resp.json().get("value", [])

async def get_meetings(room_email: str, days_back: int = 30):
    if not USE_REAL_GRAPH:
        from database import get_conn
        conn = get_conn()
        rows = conn.execute(
            "SELECT * FROM meetings WHERE room_id = ? LIMIT 100",
            (room_email,)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    from datetime import datetime, timedelta
    token = await get_token()
    start = (datetime.utcnow() - timedelta(days=days_back)).isoformat() + "Z"
    end   = datetime.utcnow().isoformat() + "Z"

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"https://graph.microsoft.com/v1.0/users/{room_email}/calendarView",
            params={
                "startDateTime": start,
                "endDateTime":   end,
                "$select":       "id,subject,start,end,attendees,isOnlineMeeting,organizer"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        return resp.json().get("value", [])