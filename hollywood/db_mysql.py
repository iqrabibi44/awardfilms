"""
Shared MySQL DB helper for all AwardFilms ingestion scripts.
Centralises connection config so only this file needs updating
when credentials change.
"""
import mysql.connector

# ─── MySQL / XAMPP credentials ───────────────────────────────────────────────
MYSQL_CONFIG = {
    "host":     "127.0.0.1",
    "port":     3306,
    "user":     "root",
    "password": "",
    "database": "awardfilms_db",
    "charset":  "utf8mb4",
    "use_unicode": True,
    "autocommit": False,
}

def get_db_connection():
    """Return a new mysql.connector connection. Caller is responsible for closing."""
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    return conn
