"""
db.py — Database connection for AwardFilms Wikipedia scraper pipeline.
Reads DATABASE_URL from scripts/.env or root .env.
"""
import os
import sys
import mysql.connector
from dotenv import load_dotenv

# Search for .env in scripts/ first, then project root
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, "..", ".."))

for env_path in [
    os.path.join(_SCRIPT_DIR, "..", ".env"),          # scripts/.env
    os.path.join(_PROJECT_ROOT, ".env.local"),         # Next.js .env.local
    os.path.join(_PROJECT_ROOT, ".env"),               # project root .env
]:
    if os.path.exists(env_path):
        load_dotenv(dotenv_path=env_path, override=False)
        break


def get_connection():
    """Return a new MySQL connection. Caller is responsible for closing."""
    try:
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="awardfilms_db"
        )
    except mysql.connector.Error as err:
        print(f"❌ Error connecting to MySQL: {err}", file=sys.stderr)
        sys.exit(1)
