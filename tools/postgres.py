# tools/postgres.py
import os
import psycopg2
from psycopg2.extras import RealDictCursor


def _get_database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is not set in environment or .env")
    return url


def run_sql(query: str, params=None, fetch: str = "auto"):
    """
    Run a SQL query on the local Postgres DB.

    fetch:
      - "all"  -> return list of rows
      - "one"  -> return single row
      - "none" -> return rowcount only
      - "auto" -> if query returns rows -> all, else rowcount
    """
    params = params or ()

    database_url = _get_database_url()

    with psycopg2.connect(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)

            if fetch == "one":
                row = cur.fetchone()
                return {"type": "one", "row": row}

            if fetch == "all":
                rows = cur.fetchall()
                return {"type": "all", "rows": rows}

            if fetch == "none":
                return {"type": "none", "rowcount": cur.rowcount}

            # auto mode
            if cur.description:  # query returned rows
                rows = cur.fetchall()
                return {"type": "all", "rows": rows}
            else:
                return {"type": "none", "rowcount": cur.rowcount}
